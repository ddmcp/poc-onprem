import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
from logger_config import setup_logger

logger = setup_logger("pg-service")

class PgService:
    def __init__(self):
        # Postgres Config
        self.db_host = os.getenv("DB_HOST", "pg-typing-pdf-extractor-db")
        self.db_name = os.getenv("DB_NAME", "pdfdb")
        self.db_user = os.getenv("DB_USER", "pdfuser")
        self.db_pass = os.getenv("DB_PASS", "pdfpassword")

    def _get_db_conn(self):
        return psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_pass
        )

    def get_chunks_to_embed(self, pdf_id: str) -> List[Dict]:
        """Fetches all chunks for a given pdf_id from Postgres."""
        conn = None
        try:
            conn = self._get_db_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT chunk_id, pdf_id, page_number, chunk_index, text FROM chunk_text WHERE pdf_id = %s ORDER BY chunk_index",
                    (pdf_id,)
                )
                return cur.fetchall()
        finally:
            if conn:
                conn.close()


    def atomic_fetch_and_lock_pdfs(self, limit: int = 5) -> List[Dict]:
        """
        Atomically fetch and lock PDFs for processing.
        Uses UPDATE...RETURNING with FOR UPDATE SKIP LOCKED to prevent race conditions.
        """
        conn = None
        try:
            conn = self._get_db_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    UPDATE pdf 
                    SET embedding_status = 'in progress'
                    WHERE pdf_id IN (
                        SELECT pdf_id FROM pdf 
                        WHERE extraction_status = 'success' AND embedding_status = 'new' 
                        LIMIT %s 
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING pdf_id, filename, bucket, extraction_status, embedding_status, created_at, embedding_started_at, embedding_completed_at;
                """
                cur.execute(query, (limit,))
                results = cur.fetchall()
            conn.commit()
            # Convert datetime to string for JSON serialization
            for r in results:
                for k in ['created_at', 'embedding_started_at', 'embedding_completed_at']:
                    if r.get(k):
                        r[k] = r[k].isoformat()
            return results
        finally:
            if conn:
                conn.close()

    def get_pdf_statuses(self, pdf_ids: List[str]) -> List[Dict]:
        """Fetches current status, metadata, timestamps, and chunk counts for a list of pdf_ids."""
        conn = None
        try:
            conn = self._get_db_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        p.pdf_id, p.filename, p.bucket, p.extraction_status, p.embedding_status, 
                        p.error_message, p.created_at, p.embedding_started_at, p.embedding_completed_at,
                        (SELECT COUNT(*) FROM chunk_text c WHERE c.pdf_id = p.pdf_id) as chunks_total
                    FROM pdf p
                    WHERE p.pdf_id = ANY(%s::uuid[])
                    """,
                    (pdf_ids,)
                )
                results = cur.fetchall()
                for r in results:
                    for k in ['created_at', 'embedding_started_at', 'embedding_completed_at']:
                        if r.get(k):
                            r[k] = r[k].isoformat()
                    r['pdf_id'] = str(r['pdf_id'])
                return results
        finally:
            if conn:
                conn.close()


    def update_embedding_status(self, pdf_id: str, status: str):
        """
        Updates embedding_status in Postgres.
        Automatically sets timestamps based on status.
        """
        conn = None
        try:
            conn = self._get_db_conn()
            with conn.cursor() as cur:
                if status == 'in progress':
                    cur.execute(
                        "UPDATE pdf SET embedding_status = %s, embedding_started_at = CURRENT_TIMESTAMP WHERE pdf_id = %s",
                        (status, pdf_id)
                    )
                elif status in ['done', 'failed']:
                    cur.execute(
                        "UPDATE pdf SET embedding_status = %s, embedding_completed_at = CURRENT_TIMESTAMP WHERE pdf_id = %s",
                        (status, pdf_id)
                    )
                else:
                    cur.execute(
                        "UPDATE pdf SET embedding_status = %s WHERE pdf_id = %s",
                        (status, pdf_id)
                    )
            conn.commit()
        finally:
            if conn:
                conn.close()