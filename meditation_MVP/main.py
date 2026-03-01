from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Import API models
from api.models import (
    TextRecommendationRequest, RecommendationResponse,
    ScriptGenerationRequest, ScriptResponse,
    AudioProcessingResponse, SessionStatusResponse, SessionResultsResponse,
    FeedbackRequest, FeedbackResponse,
    UserCreateRequest, UserResponse,
    HealthResponse, ErrorResponse
)

# Import services
from api.meditation_service import meditation_service
from api.audio_service import audio_service
from api.vector_service import vector_service

# Import database operations
from database.api_collections import (
    create_user, get_user, update_user_preferences,
    save_feedback, get_overall_analytics,
    test_api_connection, close_connections
)
from database.api_client import ExternalServiceError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Meditation API...")
    
    try:
        # Test API connection
        connected = await test_api_connection()
        if connected:
            logger.info("MeditationDB API connection successful")
        else:
            logger.warning("Failed to connect to MeditationDB API")
        
        # Initialize meditation embeddings on startup
        try:
            await vector_service.create_meditation_embeddings()
            logger.info("Meditation embeddings initialized")
        except Exception as e:
            logger.warning(f"Could not initialize meditation embeddings: {e}")
        
        logger.info("Meditation API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Meditation API...")
    try:
        await close_connections()
        logger.info("API connections closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Meditation Recommendation API",
    description="AI-powered meditation recommendations with audio analysis and TTS script generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(ExternalServiceError)
async def external_service_exception_handler(request, exc: ExternalServiceError):
    logger.error(f"External service error ({exc.status_code}): {exc}")
    # Surface 503/502/504 as-is; map other upstream errors to 502
    client_status = exc.status_code if exc.status_code in (502, 503, 504) else 502
    return JSONResponse(
        status_code=client_status,
        content={
            "error": "external_service_error",
            "message": "The meditation database service is temporarily unavailable. Please try again shortly.",
            "detail": str(exc) if os.getenv("DEBUG") else None
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, ExternalServiceError):
        return await external_service_exception_handler(request, exc)
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if os.getenv("DEBUG") else None
        }
    )

# ==================== HEALTH & INFO ENDPOINTS ====================

@app.get("/", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """API health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@app.get("/stats", tags=["Health"])
async def system_stats():
    """Get system statistics"""
    try:
        return await get_overall_analytics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# ==================== USER ENDPOINTS ====================

@app.post("/api/users", response_model=UserResponse, tags=["Users"])
async def create_new_user(user_data: UserCreateRequest):
    """Create a new user"""
    try:
        user_id = await create_user({
            'name': user_data.name,
            'email': user_data.email,
            'preferences': user_data.preferences
        })
        
        user = await get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found after creation")
        
        # Map 'id' to 'user_id' for the response model
        user['user_id'] = user.get('id', user_id)
        return UserResponse(**user)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user_profile(user_id: str):
    """Get user profile"""
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Map 'id' to 'user_id' for the response model
    user['user_id'] = user.get('id', user_id)
    return UserResponse(**user)

@app.put("/api/users/{user_id}/preferences", tags=["Users"])
async def update_preferences(user_id: str, preferences: dict):
    """Update user preferences"""
    try:
        await update_user_preferences(user_id, preferences)
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")

# ==================== MEDITATION RECOMMENDATION ENDPOINTS ====================

@app.post("/api/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_text_recommendations(request: TextRecommendationRequest):
    """Get meditation recommendations based on text input"""
    try:
        result = await meditation_service.get_text_recommendations(
            diary_text=request.diary_text,
            user_id=request.user_id
        )
        
        # Enhance with vector similarity if possible
        try:
            enhanced_recs = await vector_service.get_personalized_recommendations(
                user_id=request.user_id,
                base_recommendations=result['recommendations']
            )
            result['recommendations'] = enhanced_recs
            result['method'] = 'text_analysis_with_personalization'
        except Exception as e:
            logger.warning(f"Could not enhance recommendations: {e}")
        
        return RecommendationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@app.post("/api/generate-script", response_model=ScriptResponse, tags=["Scripts"])
async def generate_meditation_script(request: ScriptGenerationRequest):
    """Generate TTS-ready meditation script"""
    try:
        result = await meditation_service.generate_meditation_script(
            meditation_type=request.meditation_type,
            user_id=request.user_id,
            duration_minutes=request.duration_minutes
        )
        
        return ScriptResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

# ==================== AUDIO PROCESSING ENDPOINTS ====================

@app.post("/api/analyze", response_model=AudioProcessingResponse, tags=["Audio"])
async def analyze_audio(
    file: UploadFile = File(...),
    user_id: str = None,
    session_id: str = None
):
    """Upload and analyze audio file"""
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    try:
        result = await audio_service.process_audio(
            file=file,
            user_id=user_id,
            session_id=session_id
        )
        
        return AudioProcessingResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")

@app.get("/api/sessions/{session_id}/status", response_model=SessionStatusResponse, tags=["Sessions"])
async def get_session_status(session_id: str):
    """Get processing status for a session"""
    try:
        result = await audio_service.get_session_status(session_id)
        return SessionStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@app.get("/api/sessions/{session_id}/results", response_model=SessionResultsResponse, tags=["Sessions"])
async def get_session_results(session_id: str):
    """Get results for a completed session"""
    try:
        result = await audio_service.get_session_results(session_id)
        return SessionResultsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session results: {str(e)}")

@app.post("/api/enhance", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_enhanced_recommendations(
    request: TextRecommendationRequest,
    session_id: str = None
):
    """Get enhanced recommendations using both text and audio analysis"""
    
    if not session_id:
        # Just return text-based recommendations
        return await get_text_recommendations(request)
    
    try:
        # Get session results (audio analysis)
        session_result = await audio_service.get_session_results(session_id)
        
        if session_result['status'] != 'completed':
            raise HTTPException(status_code=400, detail="Audio processing not completed")
        
        # Get enhanced recommendations
        result = await meditation_service.get_enhanced_recommendations(
            diary_text=request.diary_text,
            audio_analysis=session_result['results'].get('audio_analysis', {}),
            user_id=request.user_id
        )
        
        # Further enhance with vector similarity
        try:
            enhanced_recs = await vector_service.get_personalized_recommendations(
                user_id=request.user_id,
                base_recommendations=result['recommendations']
            )
            result['recommendations'] = enhanced_recs
            result['method'] = 'multimodal_with_personalization'
        except Exception as e:
            logger.warning(f"Could not add personalization: {e}")
        
        return RecommendationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced recommendation failed: {str(e)}")

# ==================== FEEDBACK ENDPOINTS ====================

@app.post("/api/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback for a meditation session"""
    try:
        feedback_id = await save_feedback({
            'user_id': request.user_id,
            'session_id': request.session_id,
            'meditation_type': request.meditation_type,
            'rating': request.rating,
            'comment': request.comment
        })
        
        # Update user vector embedding with new feedback
        try:
            await vector_service.create_user_embedding(request.user_id)
        except Exception as e:
            logger.warning(f"Could not update user embedding: {e}")
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            message="Feedback recorded successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

# ==================== VECTOR SIMILARITY ENDPOINTS ====================

@app.get("/api/users/{user_id}/similar", tags=["Recommendations"])
async def find_similar_users(user_id: str, limit: int = 5):
    """Find users similar to the given user"""
    try:
        similar_users = await vector_service.find_similar_users(user_id, limit)
        return {"user_id": user_id, "similar_users": similar_users}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar users: {str(e)}")

@app.post("/api/vectors/create-user", tags=["Vectors"])
async def create_user_vector(user_id: str):
    """Create or update user embedding vector"""
    try:
        vector_id = await vector_service.create_user_embedding(user_id)
        return {"message": "User embedding created", "vector_id": vector_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user vector: {str(e)}")

# ==================== DEVELOPMENT ENDPOINTS ====================

if os.getenv("DEBUG"):
    
    @app.get("/dev/test-recommendation", tags=["Development"])
    async def test_recommendation():
        """Test endpoint for development"""
        test_request = TextRecommendationRequest(
            diary_text="Feeling stressed and anxious about work",
            user_id="dev_test_user"
        )
        return await get_text_recommendations(test_request)
    
    @app.get("/dev/meditation-types", tags=["Development"])
    async def list_meditation_types():
        """List all available meditation types"""
        return {
            "meditation_types": meditation_service.meditation_data['Name'].tolist(),
            "count": len(meditation_service.meditation_data)
        }

# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Meditation API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        os.environ["DEBUG"] = "1"
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info" if not args.debug else "debug"
    )