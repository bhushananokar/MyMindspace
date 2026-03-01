# api_service.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from pydantic import BaseModel
from datetime import datetime
import logging
from integration_main import AstraDBIntegrator

app = FastAPI(title="Journal Processing API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173","*"],  # Your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

logger = logging.getLogger(__name__)

class JournalProcessRequest(BaseModel):
    journal_id: str
    user_id: str
    trigger_immediate: bool = True

class JournalProcessResponse(BaseModel):
    success: bool
    message: str
    processing_time_ms: float = None
    entry_id: str = None

class UserHistoryContextRequest(BaseModel):
    user_id: str

class UserHistoryContextResponse(BaseModel):
    success: bool
    message: str
    user_history_context: dict = None

# Initialize your integrator
integrator = AstraDBIntegrator()

@app.post("/process-journal", response_model=JournalProcessResponse)
async def process_journal_entry(
    request: JournalProcessRequest,
    background_tasks: BackgroundTasks
):
    """Process a journal entry and store embeddings"""
    try:
        if request.trigger_immediate:
            # Process immediately
            result = integrator.process_specific_journal_from_db(
                journal_id=request.journal_id,
                push_to_astra=True
            )
            
            if result:
                return JournalProcessResponse(
                    success=True,
                    message="Journal processed and embeddings stored successfully",
                    processing_time_ms=result.processing_time_ms,
                    entry_id=request.journal_id
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Journal entry not found or processing failed"
                )
        else:
            # Process in background
            background_tasks.add_task(
                process_journal_background,
                request.journal_id
            )
            return JournalProcessResponse(
                success=True,
                message="Journal processing queued successfully",
                entry_id=request.journal_id
            )
            
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_journal_background(journal_id: str):
    """Background task for processing journal entries"""
    try:
        integrator.process_specific_journal_from_db(
            journal_id=journal_id,
            push_to_astra=True
        )
        logger.info(f"Background processing completed for {journal_id}")
    except Exception as e:
        logger.error(f"Background processing failed for {journal_id}: {e}")

@app.get("/user-history-context/{user_id}", response_model=UserHistoryContextResponse)
async def get_user_history_context(user_id: str):
    """Get user history context for a specific user"""
    try:
        user_history_context = integrator.user_history_client.get_user_history_context(user_id)
        
        if user_history_context:
            return UserHistoryContextResponse(
                success=True,
                message="User history context retrieved successfully",
                user_history_context=user_history_context
            )
        else:
            return UserHistoryContextResponse(
                success=False,
                message="No user history context found for this user",
                user_history_context=None
            )
            
    except Exception as e:
        logger.error(f"Failed to retrieve user history context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "journal-processing-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
