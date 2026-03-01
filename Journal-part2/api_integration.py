#!/usr/bin/env python3
"""
Gemini Engine FastAPI Integration
Complete LSTM Memory → Conversation Engine → Gemini AI Response Workflow
Based on full_demo.ipynb notebook implementation
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import traceback
from dotenv import load_dotenv

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
comp5_path = os.path.join(project_root, 'comp5')

# Global variables for components
orchestrator = None
bridge = None

# Pydantic Models for API
class EmotionalState(BaseModel):
    """User's emotional state for context-aware responses"""
    primary_emotion: str = Field(..., description="Primary emotion (e.g., 'excited', 'sad', 'happy', 'angry')", example="excited")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Emotion intensity from 0.0 (weak) to 1.0 (strong)", example=0.8)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Confidence in emotion detection from 0.0 to 1.0", example=0.9)

class ConversationRequest(BaseModel):
    """Main conversation request for processing through Gemini Engine workflow"""
    user_id: str = Field(..., description="Unique user identifier", example="user_12345")
    user_message: str = Field(..., description="User's message or query", example="I'm feeling excited about my new AI project!")
    conversation_id: str = Field(..., description="Unique conversation identifier", example="conv_001")
    emotional_state: Optional[EmotionalState] = Field(default=None, description="User's emotional state for context-aware responses")
    max_memories: int = Field(default=10, ge=1, le=50, description="Maximum number of memories to retrieve from LSTM gates", example=10)
    include_analysis: bool = Field(default=True, description="Include detailed response analysis and quality metrics")

class MemoryContextRequest(BaseModel):
    """Request for LSTM memory context retrieval"""
    user_id: str = Field(..., description="Unique user identifier", example="user_12345")
    current_message: str = Field(..., description="Current user message for memory retrieval", example="How am I feeling about work lately?")
    conversation_id: str = Field(..., description="Unique conversation identifier", example="conv_001")
    max_memories: int = Field(default=10, ge=1, le=50, description="Maximum number of memories to retrieve", example=10)

class HealthCheckResponse(BaseModel):
    """System health check response"""
    overall_healthy: bool = Field(..., description="Overall system health status")
    component_health: Dict[str, Any] = Field(..., description="Individual component health status")
    system_metrics: Dict[str, Any] = Field(..., description="System performance metrics")
    timestamp: str = Field(..., description="Health check timestamp")

class PerformanceResponse(BaseModel):
    """Performance metrics response"""
    conversation_metrics: Dict[str, Any] = Field(..., description="Conversation processing metrics")
    component5_stats: Dict[str, Any] = Field(..., description="Component 5 (LSTM Memory) statistics")
    component6_stats: Dict[str, Any] = Field(..., description="Component 6 (Conversation Engine) statistics")
    component7_stats: Dict[str, Any] = Field(..., description="Component 7 (Quality Analysis) statistics")
    timestamp: str = Field(..., description="Performance metrics timestamp")

class ConversationResponse(BaseModel):
    """Complete conversation response with all metadata"""
    response_id: str = Field(..., description="Unique response identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    enhanced_response: str = Field(..., description="AI-generated enhanced response")
    original_response: Optional[str] = Field(None, description="Original response before enhancement")
    processing_timestamp: str = Field(..., description="Response processing timestamp")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    quality_metrics: Optional[Dict[str, Any]] = Field(None, description="Response quality analysis metrics")
    safety_checks: Optional[Dict[str, Any]] = Field(None, description="Safety and content filtering results")
    context_usage: Optional[Dict[str, Any]] = Field(None, description="Memory context usage statistics")
    response_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    follow_up_suggestions: Optional[List[str]] = Field(None, description="AI-generated follow-up conversation suggestions")
    proactive_suggestions: Optional[List[str]] = Field(None, description="Proactive engagement suggestions")
    memory_context_metadata: Optional[Dict[str, Any]] = Field(None, description="LSTM memory retrieval metadata")
    enhancement_metadata: Optional[Dict[str, Any]] = Field(None, description="Response enhancement processing metadata")

class MemoryContextResponse(BaseModel):
    """LSTM memory context retrieval response"""
    selected_memories: List[Dict[str, Any]] = Field(..., description="Retrieved memories from LSTM gates")
    relevance_scores: List[float] = Field(..., description="Relevance scores for each memory")
    token_usage: int = Field(..., description="Token usage for memory processing")
    assembly_metadata: Dict[str, Any] = Field(..., description="Memory assembly metadata")
    retrieval_time_ms: float = Field(..., description="Memory retrieval time in milliseconds")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type/class")
    timestamp: str = Field(..., description="Error timestamp")
    traceback: Optional[str] = Field(None, description="Error traceback for debugging")

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for component initialization and cleanup"""
    global orchestrator, bridge
    
    print("🚀 Starting Gemini Engine FastAPI Integration...")
    
    try:
        # Initialize components
        await initialize_components()
        print("✅ All components initialized successfully")
        
        yield
        
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        raise
    finally:
        # Cleanup
        print("🧹 Cleaning up resources...")
        await cleanup_components()
        print("✅ Cleanup completed")

# FastAPI app with comprehensive documentation
app = FastAPI(
    title="Gemini Engine API",
    description="""
    ## 🧠 Complete LSTM Memory → Conversation Engine → Gemini AI Response Workflow
    
    This API provides a complete integration of the Gemini Engine system, following the exact implementation from the `full_demo.ipynb` notebook.
    
    ### 🔄 Workflow Process:
    1. **LSTM Memory Retrieval (Component 5)**: Uses LSTM gates to retrieve relevant memories from AstraDB
    2. **Context Assembly (Component 6)**: Assembles context with memories and user query
    3. **Gemini AI Response**: Generates AI response using Google's Gemini model
    4. **Quality Analysis (Component 7)**: Analyzes response quality and user satisfaction
    
    ### 🎯 Key Features:
    - **Real-time Memory Retrieval**: LSTM gates retrieve relevant memories based on user queries
    - **Context-Aware Responses**: Emotional state and memory context inform AI responses
    - **Quality Analysis**: Comprehensive response quality and user satisfaction tracking
    - **Batch Processing**: Support for multiple conversations
    - **Performance Monitoring**: Detailed metrics and health checks
    
    ### 🔧 Components:
    - **Component 5**: LSTM Memory Gates for intelligent memory retrieval
    - **Component 6**: Conversation Engine for context assembly and Gemini integration
    - **Component 7**: Quality Analysis for response evaluation and improvement
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Component initialization
async def initialize_components():
    """Initialize all Gemini Engine components"""
    global orchestrator, bridge
    
    try:
        # Import required modules
        from component6.comp5_interface import Component5Bridge
        from gemini_engine_orchestrator import GeminiEngineOrchestrator
        
        # Initialize Component 5 Bridge (LSTM Memory Gates)
        print("🧠 Initializing Component 5 Bridge (LSTM Memory Gates)...")
        bridge = Component5Bridge()
        bridge_init_success = await bridge.initialize()
        
        if not bridge_init_success:
            raise Exception("Failed to initialize Component 5 Bridge")
        
        print("✅ Component 5 Bridge initialized")
        
        # Initialize Gemini Engine Orchestrator
        print("🎼 Initializing Gemini Engine Orchestrator...")
        orchestrator = GeminiEngineOrchestrator()
        orchestrator_init_success = await orchestrator.initialize()
        
        if not orchestrator_init_success:
            raise Exception("Failed to initialize Gemini Engine Orchestrator")
        
        print("✅ Gemini Engine Orchestrator initialized")
        
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        raise

# Component cleanup
async def cleanup_components():
    """Cleanup all components"""
    global orchestrator, bridge
    
    try:
        if orchestrator:
            await orchestrator.cleanup()
        if bridge:
            await bridge.cleanup()
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

# Dependency injection
async def get_orchestrator():
    """Get orchestrator instance"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return orchestrator

async def get_bridge():
    """Get bridge instance"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    return bridge

# API Endpoints

@app.get("/", 
         response_model=Dict[str, str],
         summary="Root Endpoint",
         description="Get basic API information and status")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Gemini Engine API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "description": "Complete LSTM Memory → Conversation Engine → Gemini AI Response Workflow"
    }

@app.get("/health", 
         response_model=HealthCheckResponse,
         summary="System Health Check",
         description="Check the health status of all Gemini Engine components including Component 5 (LSTM), Component 6 (Conversation Engine), and Component 7 (Quality Analysis)")
async def health_check(orch: Any = Depends(get_orchestrator)):
    """Comprehensive health check for all system components"""
    try:
        health = await orch.health_check()
        
        return HealthCheckResponse(
            overall_healthy=health.get('overall_healthy', False),
            component_health=health.get('component_health', {}),
            system_metrics=health.get('system_metrics', {}),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/performance", 
         response_model=PerformanceResponse,
         summary="Performance Metrics",
         description="Get comprehensive performance metrics for all components including conversation processing, memory retrieval, and quality analysis statistics")
async def get_performance_metrics(orch: Any = Depends(get_orchestrator)):
    """Get detailed performance metrics for all system components"""
    try:
        performance = orch.get_performance_summary()
        
        return PerformanceResponse(
            conversation_metrics=performance.get('conversation_metrics', {}),
            component5_stats=performance.get('component5_stats', {}),
            component6_stats=performance.get('component6_stats', {}),
            component7_stats=performance.get('component7_stats', {}),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance metrics retrieval failed: {str(e)}")

@app.post("/memory/context", 
          response_model=MemoryContextResponse,
          summary="LSTM Memory Retrieval",
          description="Retrieve relevant memories using LSTM gates from Component 5. This endpoint demonstrates the LSTM memory retrieval process that happens before conversation processing.")
async def get_memory_context(
    request: MemoryContextRequest,
    brdg: Any = Depends(get_bridge)
):
    """Get LSTM memory context for a user query using Component 5"""
    try:
        start_time = datetime.utcnow()
        
        # Get memory context using LSTM gates
        memory_context = await brdg.get_memory_context(
            user_id=request.user_id,
            current_message=request.current_message,
            conversation_id=request.conversation_id,
            max_memories=request.max_memories
        )
        
        retrieval_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return MemoryContextResponse(
            selected_memories=memory_context.selected_memories,
            relevance_scores=memory_context.relevance_scores,
            token_usage=memory_context.token_usage,
            assembly_metadata=memory_context.assembly_metadata,
            retrieval_time_ms=retrieval_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Memory context retrieval failed: {str(e)}"
        )

@app.post("/conversation", 
          response_model=ConversationResponse,
          summary="Complete Conversation Processing",
          description="""
          Process a complete conversation through the entire Gemini Engine workflow:
          
          ### 🔄 Processing Steps:
          1. **LSTM Memory Retrieval (Component 5)**: Retrieve relevant memories using LSTM gates
          2. **Context Assembly (Component 6)**: Assemble context with memories and user query
          3. **Gemini AI Response**: Generate AI response using Google's Gemini model
          4. **Quality Analysis (Component 7)**: Analyze response quality and user satisfaction
          
          ### 📊 Response Includes:
          - Enhanced AI response with memory context
          - Quality metrics and analysis
          - Memory usage statistics
          - Follow-up suggestions
          - Processing time and performance data
          """)
async def process_conversation(
    request: ConversationRequest,
    background_tasks: BackgroundTasks,
    orch: Any = Depends(get_orchestrator)
):
    """Process a complete conversation through the Gemini Engine workflow"""
    try:
        start_time = datetime.utcnow()
        
        # Process conversation through orchestrator
        response = await orch.process_conversation(
            user_id=request.user_id,
            user_message=request.user_message,
            conversation_id=request.conversation_id,
            emotional_state=request.emotional_state.dict() if request.emotional_state else None
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract response data
        response_data = {
            "response_id": response.response_id,
            "conversation_id": response.conversation_id,
            "user_id": response.user_id,
            "enhanced_response": response.enhanced_response,
            "original_response": getattr(response, 'original_response', None),
            "processing_timestamp": response.processing_timestamp.isoformat() if hasattr(response, 'processing_timestamp') else datetime.now().isoformat(),
            "processing_time_ms": processing_time,
            "quality_metrics": getattr(response, 'quality_metrics', None),
            "safety_checks": getattr(response, 'safety_checks', None),
            "context_usage": getattr(response, 'context_usage', None),
            "response_metadata": getattr(response, 'response_metadata', None),
            "follow_up_suggestions": getattr(response, 'follow_up_suggestions', None),
            "proactive_suggestions": getattr(response, 'proactive_suggestions', None),
            "memory_context_metadata": getattr(response, 'memory_context_metadata', None),
            "enhancement_metadata": getattr(response, 'enhancement_metadata', None)
        }
        
        # Add response analysis if available and requested
        if request.include_analysis and hasattr(response, 'response_analysis') and response.response_analysis:
            analysis = response.response_analysis
            if hasattr(analysis, 'quality_scores'):
                response_data["quality_metrics"] = analysis.quality_scores
            if hasattr(analysis, 'user_satisfaction'):
                response_data["user_satisfaction"] = analysis.user_satisfaction
            if hasattr(analysis, 'context_usage'):
                response_data["context_usage"] = analysis.context_usage
            if hasattr(analysis, 'improvement_suggestions'):
                response_data["improvement_suggestions"] = analysis.improvement_suggestions
        
        return ConversationResponse(**response_data)
        
    except Exception as e:
        # Log the error for debugging
        error_traceback = traceback.format_exc()
        print(f"❌ Conversation processing failed: {e}")
        print(f"Traceback: {error_traceback}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Conversation processing failed: {str(e)}"
        )

@app.post("/conversation/batch", 
          response_model=List[ConversationResponse],
          summary="Batch Conversation Processing",
          description="Process multiple conversations in batch. Each conversation goes through the complete workflow: LSTM Memory Retrieval → Context Assembly → Gemini AI Response → Quality Analysis")
async def process_batch_conversations(
    requests: List[ConversationRequest],
    background_tasks: BackgroundTasks,
    orch: Any = Depends(get_orchestrator)
):
    """Process multiple conversations in batch"""
    try:
        results = []
        
        for request in requests:
            try:
                # Process each conversation
                response = await process_conversation(request, background_tasks, orch)
                results.append(response)
            except Exception as e:
                # Create error response for failed conversation
                error_response = ConversationResponse(
                    response_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    conversation_id=request.conversation_id,
                    user_id=request.user_id,
                    enhanced_response=f"Error processing conversation: {str(e)}",
                    processing_timestamp=datetime.now().isoformat(),
                    processing_time_ms=0.0,
                    response_metadata={"error": str(e), "status": "failed"}
                )
                results.append(error_response)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch conversation processing failed: {str(e)}"
        )

@app.post("/test/integration",
          summary="Run Integration Test",
          description="Run the complete integration test suite from integration_main.py to verify all components are working correctly")
async def run_integration_test(background_tasks: BackgroundTasks):
    """Run complete integration test suite"""
    try:
        from integration_main import run_full_integration_test
        
        # Run integration test in background
        background_tasks.add_task(run_full_integration_test)
        
        return {
            "message": "Integration test started in background",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "description": "Complete integration test suite is running. Check logs for detailed results."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Integration test failed: {str(e)}"
        )

@app.get("/test/health",
         summary="Detailed Health Test",
         description="Comprehensive health check with detailed component status, performance metrics, and system diagnostics")
async def test_health_check(orch: Any = Depends(get_orchestrator)):
    """Test health check with detailed component status"""
    try:
        health = await orch.health_check()
        
        # Get performance metrics
        performance = orch.get_performance_summary()
        
        return {
            "health_status": health,
            "performance_metrics": performance,
            "timestamp": datetime.now().isoformat(),
            "status": "healthy" if health.get('overall_healthy', False) else "unhealthy",
            "description": "Comprehensive system health and performance diagnostics"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "description": "Health check failed - system may be experiencing issues"
        }

@app.post("/memory/retrieve",
          summary="Direct Memory Retrieval",
          description="Direct memory retrieval using LSTM gates from Component 5. This endpoint bypasses the full conversation workflow and focuses only on memory retrieval.")
async def retrieve_memories(
    request: MemoryContextRequest,
    brdg: Any = Depends(get_bridge)
):
    """Retrieve memories for a user using LSTM gates"""
    try:
        start_time = datetime.utcnow()
        
        memory_context = await brdg.get_memory_context(
            user_id=request.user_id,
            current_message=request.current_message,
            conversation_id=request.conversation_id,
            max_memories=request.max_memories
        )
        
        retrieval_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
            "memories_retrieved": len(memory_context.selected_memories),
            "memories": memory_context.selected_memories,
            "relevance_scores": memory_context.relevance_scores,
            "token_usage": memory_context.token_usage,
            "assembly_metadata": memory_context.assembly_metadata,
            "retrieval_time_ms": retrieval_time,
            "timestamp": datetime.now().isoformat(),
            "description": "LSTM memory retrieval completed successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Memory retrieval failed: {str(e)}"
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with detailed error information"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_type": "HTTPException",
            "timestamp": datetime.now().isoformat(),
            "description": "HTTP error occurred during request processing"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with comprehensive error details"""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc(),
            "description": "Internal server error occurred"
        }
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    print("🚀 Gemini Engine FastAPI Integration Starting...")
    print("📚 API Documentation available at: http://localhost:8007/docs")
    print("🔧 ReDoc Documentation available at: http://localhost:8007/redoc")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    print("🧹 Gemini Engine FastAPI Integration Shutting Down...")
    await cleanup_components()

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Gemini Engine FastAPI Integration...")
    print("📚 Swagger UI Documentation: http://localhost:8007/docs")
    print("📖 ReDoc Documentation: http://localhost:8007/redoc")
    print("🔧 Health Check: http://localhost:8007/health")
    print("📊 Performance Metrics: http://localhost:8007/performance")
    
    # Run the FastAPI application
    uvicorn.run(
        "api_integration:app",
        host="0.0.0.0",
        port=8007,
        reload=True,
        log_level="info"
    )
