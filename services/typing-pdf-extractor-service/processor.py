import os
import fitz  # PyMuPDF
from typing import List, Dict, Optional, Any
from minio import Minio
from minio.error import S3Error
from persistence import TextDataPersistenceService
from logger_config import setup_logger

logger = setup_logger("pdf-processor")

class PdfProcessor:
    def __init__(self):
        # MinIO config
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        self.minio_user = os.getenv("MINIO_ROOT_USER", "minioadmin")
        self.minio_pass = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
        self.minio_secure = os.getenv("MINIO_SECURE", "False").lower() == "true"
        
        self.default_chunk_size = int(os.getenv("DEFAULT_CHUNK_SIZE", 500))
        self.default_chunk_overlap = int(os.getenv("DEFAULT_CHUNK_OVERLAP", 50))

        logger.info(f"Initializing MinIO client connection to {self.minio_endpoint}")
        self.minio_client = Minio(
            self.minio_endpoint,
            access_key=self.minio_user,
            secret_key=self.minio_pass,
            secure=self.minio_secure
        )
        
        self.persistence_service = TextDataPersistenceService()

    def download_file(self, bucket_name: str, object_name: str, local_path: str):
        """Downloads a file from MinIO to a local path."""
        logger.info(f"Downloading {object_name} from bucket {bucket_name}...")
        try:
            self.minio_client.fget_object(bucket_name, object_name, local_path)
        except Exception as e:
            logger.error(f"MinIO download error: {str(e)}")
            raise

    def extract_and_chunk(self, pdf_path: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Extracts text from PDF and splits it into chunks, preserving page references."""
        logger.info(f"Extracting and chunking PDF: {pdf_path}")
        chunks = []
        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc, start=1):
                    text = page.get_text()
                    if not text.strip():
                        continue
                    
                    # Page-level chunking
                    start = 0
                    chunk_idx = 0
                    while start < len(text):
                        end = start + chunk_size
                        chunk_text = text[start:end]
                        chunks.append({
                            "page_number": page_num,
                            "chunk_index": chunk_idx,
                            "text": chunk_text
                        })
                        start += chunk_size - overlap
                        chunk_idx += 1
                        if overlap >= chunk_size:
                            break
            return chunks
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise

    def process_pdf(self, file_path: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None) -> Any:
        """
        Orchestrates the PDF processing pipeline:
        1. Parse file path (bucket/object)
        2. Download from MinIO
        3. Extract text and metadata
        4. Chunk text
        5. Persist to SQL Database
        """
        if "/" not in file_path:
            raise ValueError("Invalid file_path format. Expected 'bucket/object_name'")
        
        bucket_name, object_name = file_path.split("/", 1)
        temp_pdf = f"/tmp/{os.path.basename(object_name)}"
        
        c_size = chunk_size or self.default_chunk_size
        c_overlap = overlap or self.default_chunk_overlap
        pdf_id = None
        try:
            # 0. Create/Update PDF record immediately for error tracking
            # This call now handles locking and status checking.
            record = self.persistence_service.upsert_pdf_record(bucket_name, object_name)
            pdf_id = str(record['pdf_id'])
            
            if record.get('extraction_status') == 'success':
                logger.info(f"Skipping already processed file: {file_path}")
                return pdf_id
            
            # 1. Download
            self.download_file(bucket_name, object_name, temp_pdf)
            
            # 2. Extract Metadata
            with fitz.open(temp_pdf) as doc:
                metadata = doc.metadata
            
            # 3. Extract and Chunk Text
            chunks = self.extract_and_chunk(temp_pdf, c_size, c_overlap)
            
            # 4. Save to SQL Database
            self.persistence_service.save_pdf_data(pdf_id, metadata, chunks)                        
            
            # 5. Final Status Update
            self.persistence_service.update_extraction_status(pdf_id, "success")
            
            return pdf_id
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Processing failed for {file_path}: {error_msg}")
            
            # Record failure in DB if we have the pdf_id
            if pdf_id:
                try:
                    self.persistence_service.update_extraction_status(pdf_id, "failed", error_msg)
                except Exception as db_err:
                    logger.error(f"Failed to record error status in DB: {str(db_err)}")
            raise
        finally:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
