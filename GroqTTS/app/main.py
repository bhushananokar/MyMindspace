"""
Main FastAPI application for TTS microservice.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config.settings import settings
from .websocket.tts_handler import tts_websocket_handler
from .services.audio_generator import audio_generator
from .models.tts_model import tts_model

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting TTS microservice...")
    
    # Validate configuration
    if settings.use_groq and not settings.groq_api_key:
        logger.warning("⚠️ GROQ_API_KEY not found - please check your .env file")
        logger.warning("Create a .env file from .env.example and set your Groq API key")
    
    try:
        await audio_generator.initialize()
        logger.info("✅ TTS microservice started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start TTS microservice: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down TTS microservice...")
    try:
        tts_model.cleanup()
    except:
        pass
    logger.info("TTS microservice shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="TTS Microservice",
    description="WebSocket-based Text-to-Speech microservice using Orpheus 3B model",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "TTS Microservice",
        "version": "1.0.0",
        "status": "running",
        "model_type": "groq" if settings.use_groq else "local",
        "model": settings.groq_model if settings.use_groq else settings.model_name,
        "default_voice": settings.groq_voice if settings.use_groq else settings.default_voice,
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "websocket": "/ws/tts",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        model_status = "loaded" if audio_generator.is_initialized else "not_loaded"
        
        return {
            "status": "healthy",
            "model_status": model_status,
            "model_type": "groq" if settings.use_groq else "local",
            "groq_configured": bool(settings.groq_api_key),
            "active_connections": len(tts_websocket_handler.manager.active_connections),
            "max_connections": settings.max_concurrent_connections,
            "configuration": {
                "model": settings.groq_model if settings.use_groq else settings.model_name,
                "default_voice": settings.groq_voice if settings.use_groq else settings.default_voice,
                "sample_rate": settings.sample_rate,
                "use_groq": settings.use_groq
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.get("/status")
async def get_status():
    """Detailed status endpoint."""
    return {
        "service_info": {
            "name": "TTS Microservice",
            "version": "1.0.0",
            "model_type": "groq" if settings.use_groq else "local",
            "model": settings.groq_model if settings.use_groq else settings.model_name,
            "voice": settings.groq_voice if settings.use_groq else settings.default_voice
        },
        "performance": {
            "active_connections": len(tts_websocket_handler.manager.active_connections),
            "max_connections": settings.max_concurrent_connections,
            "model_loaded": audio_generator.is_initialized
        },
        "configuration": {
            "use_groq": settings.use_groq,
            "groq_configured": bool(settings.groq_api_key),
            "sample_rate": settings.sample_rate,
            "max_text_length": settings.max_text_length,
            "chunk_size": settings.chunk_size,
            "chunk_size_words": settings.chunk_size_words,
            "chunk_timeout": settings.chunk_timeout_seconds
        }
    }


@app.websocket("/ws/tts")
async def websocket_tts_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for TTS streaming."""
    # Configure WebSocket timeout
    websocket.client_state = websocket.client_state
    await tts_websocket_handler.handle_connection(websocket)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting TTS microservice on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )