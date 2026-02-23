import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Dict, Optional, Any
import hashlib
from logger_config import setup_logger

logger = setup_logger("persistence-service")

class TextDataPersistenceService:
    def __init__(self):
        # Database config from environment
        self.db_host = os.getenv("DB_HOST", "pg-typing-pdf-extractor-db")
        self.db_name = os.getenv("DB_NAME", "pdfdb")
        self.db_user = os.getenv("DB_USER", "pdfuser")
        self.db_pass = os.getenv("DB_PASS", "pdfpassword")

    def _get_db_conn(self):
        """Creates and returns a new database connection."""
        return psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_pass
        )

    def _get_lock_id(self, bucket: str, filename: str) -> int:
        """Generates a stable 64-bit integer ID for a bucket/filename pair for advisory locks."""
        key = f"{bucket}/{filename}"
        # PostgreSQL advisory locks take a 64-bit bigint.
        # We take the first 8 bytes of a SHA-256 hash.
        hash_val = hashlib.sha256(key.encode()).digest()
        return int.from_bytes(hash_val[:8], byteorder='big', signed=True)

    def save_pdf_data(self, pdf_id: str, metadata: Dict, chunks: List[Dict]) -> List[str]:
        """
        Orchestrates the persistence of PDF metadata and text chunks for an existing PDF record.
        Returns a list of chunk IDs.
        """
        logger.info(f"Persisting metadata and chunks for PDF {pdf_id}...")
        conn = None
        try:
            conn = self._get_db_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. Upsert Metadata
                self._upsert_metadata(cur, pdf_id, metadata)

                # 2. Save Chunks and get their IDs
                chunk_ids = self._save_chunks(cur, pdf_id, chunks)

            conn.commit()
            logger.info(f"Successfully persisted metadata and {len(chunks)} chunks for PDF {pdf_id}.")
            return [str(cid) for cid in chunk_ids]
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database persistence error for PDF {pdf_id}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def delete_pdf_data(self, pdf_id: str):
        """
        Deletes all data associated with a pdf_id from the database.
        Used for rollbacks in case of processing failures.
        """
        logger.warning(f"Rolling back SQL data for PDF {pdf_id}...")
        conn = None
        try:
            conn = self._get_db_conn()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chunk_text WHERE pdf_id = %s", (pdf_id,))
                cur.execute("DELETE FROM pdf_metadata WHERE pdf_id = %s", (pdf_id,))
                cur.execute("DELETE FROM pdf WHERE pdf_id = %s", (pdf_id,))
            conn.commit()
            logger.info(f"Successfully deleted SQL data for PDF {pdf_id}.")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error during SQL rollback for PDF {pdf_id}: {str(e)}")
        finally:
            if conn:
                conn.close()

    def upsert_pdf_record(self, bucket: str, filename: str) -> Dict[str, Any]:
        """
        Inserts or updates the PDF entry and returns the record including status.
        Now also includes checking if it's already successful to allow skipping.
        """
        conn = None
        try:
            conn = self._get_db_conn()
            lock_id = self._get_lock_id(bucket, filename)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Acquire a transaction-level advisory lock. 
                # This will block other transactions trying to acquire the same lock.
                logger.info(f"Acquiring advisory lock for {bucket}/{filename} (ID: {lock_id})")
                cur.execute("SELECT pg_advisory_xact_lock(%s)", (lock_id,))
                
                # Check current status first
                cur.execute(
                    "SELECT pdf_id, extraction_status FROM pdf WHERE bucket = %s AND filename = %s",
                    (bucket, filename)
                )
                row = cur.fetchone()
                
                if row and row['extraction_status'] == 'success':
                    logger.info(f"PDF {filename} in bucket {bucket} already successfully extracted.")
                    return row

                # Upsert to processing status
                cur.execute(
                    """
                    INSERT INTO pdf (filename, bucket, extraction_status, error_message) 
                    VALUES (%s, %s, 'processing', NULL) 
                    ON CONFLICT (filename, bucket) 
                    DO UPDATE SET 
                        extraction_status = 'processing',
                        error_message = NULL
                    RETURNING pdf_id, extraction_status;
                    """,
                    (filename, bucket)
                )
                result = cur.fetchone()
            conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error upserting PDF record for {filename}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def _upsert_pdf(self, cur, bucket: str, filename: str) -> str:
        """Internal helper for upserting PDF within a transaction."""
        cur.execute(
            """
            INSERT INTO pdf (filename, bucket, extraction_status, error_message) 
            VALUES (%s, %s, 'processing', NULL) 
            ON CONFLICT (filename, bucket) 
            DO UPDATE SET 
                extraction_status = 'processing',
                error_message = NULL
            RETURNING pdf_id;
            """,
            (filename, bucket)
        )
        return cur.fetchone()['pdf_id']

    def update_extraction_status(self, pdf_id: str, status: str, error: str = None):
        """Updates the extraction_status and error_message for a PDF."""
        logger.info(f"Updating extraction status for {pdf_id} to '{status}'...")
        conn = None
        try:
            conn = self._get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pdf SET extraction_status = %s, error_message = %s WHERE pdf_id = %s",
                    (status, error, pdf_id)
                )
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating extraction status for {pdf_id}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def _upsert_metadata(self, cur, pdf_id: str, metadata: Dict):
        """Inserts or updates the PDF metadata."""
        cur.execute(
            """
            INSERT INTO pdf_metadata (pdf_id, creator, lineage, document_type, language, extra)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (pdf_id) DO UPDATE SET 
                creator = EXCLUDED.creator,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (
                pdf_id, 
                metadata.get("creator"), 
                "pdf_typing_microservice", 
                "pdf", 
                metadata.get("language", "unknown"),
                Json(metadata)
            )
        )

    def _save_chunks(self, cur, pdf_id: str, chunks: List[Dict]) -> List[str]:
        """Clears existing chunks, inserts new ones, and returns the generated UUIDs."""
        cur.execute("DELETE FROM chunk_text WHERE pdf_id = %s", (pdf_id,))
        chunk_ids = []
        for chunk in chunks:
            cur.execute(
                """
                INSERT INTO chunk_text (pdf_id, page_number, chunk_index, text)
                VALUES (%s, %s, %s, %s)
                RETURNING chunk_id;
                """,
                (pdf_id, chunk.get("page_number", 0), chunk.get("chunk_index"), chunk.get("text"))
            )
            chunk_ids.append(cur.fetchone()['chunk_id'])
        return chunk_ids
