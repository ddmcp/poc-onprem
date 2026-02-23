from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from processor import EmbeddingProcessor
from logger_config import setup_logger

logger = setup_logger("api-server")
app = FastAPI(title="Embedding Service")
processor = EmbeddingProcessor()

class BatchRequest(BaseModel):
    limit: int = 2

class StatusRequest(BaseModel):
    pdf_ids: List[str]

@app.post("/process-batch")
async def process_batch(background_tasks: BackgroundTasks, request: BatchRequest = BatchRequest()):
    """
    Endpoint to process a batch of new PDFs.
    Atomically fetches and locks PDFs, then returns technical details immediately.
    Actual processing happens in the background.
    """
    logger.info(f"Received batch processing request (limit={request.limit})")
    
    # 1. Atomically fetch and lock
    pdfs = processor.fetch_batch_to_process(request.limit)
    
    if not pdfs:
        return {"message": "No new PDFs to process", "pdfs": []}
    
    # 2. Schedule background processing
    background_tasks.add_task(processor.process_locked_pdfs_background, pdfs)
    
    # 3. Return immediately
    return {
        "message": f"Processing started for {len(pdfs)} PDFs",
        "pdfs": pdfs
    }

@app.post("/status")
async def get_statuses(request: StatusRequest):
    """
    Returns statuses and metadata for a list of PDF IDs.
    """
    logger.info(f"Received status request for {len(request.pdf_ids)} PDFs")
    return processor.get_bulk_statuses(request.pdf_ids)

@app.get("/health")
async def health():
    return {"status": "healthy"}
