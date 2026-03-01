# Gemini Engine FastAPI Integration Documentation

## 🚀 Overview

The Gemini Engine FastAPI Integration provides a complete REST API for the LSTM Memory → Conversation Engine → Gemini AI Response workflow. This API follows the exact implementation from the `full_demo.ipynb` notebook.

## 🏗️ Architecture

```
User Query → LSTM Memory Retrieval (Component 5) → Context Assembly (Component 6) → Gemini AI Response → Quality Analysis (Component 7)
```

## 📋 API Endpoints

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔗 Core Endpoints

### 1. **POST /conversation** - Main Conversation Processing
Process a complete conversation through the Gemini Engine workflow.

**Request Body:**
```json
{
  "user_id": "string",
  "user_message": "string", 
  "conversation_id": "string",
  "emotional_state": {
    "primary_emotion": "excited",
    "intensity": 0.8,
    "confidence": 0.9
  },
  "max_memories": 10,
  "include_analysis": true
}
```

**Response:**
```json
{
  "response_id": "resp_12345",
  "conversation_id": "conv_001",
  "user_id": "user_123",
  "enhanced_response": "AI generated response...",
  "processing_timestamp": "2025-01-01T12:00:00Z",
  "processing_time_ms": 1500.5,
  "quality_metrics": {
    "overall_quality": 0.85,
    "coherence_score": 0.9,
    "relevance_score": 0.8
  },
  "memory_context_metadata": {
    "memories_used": 5,
    "retrieval_time_ms": 200.3
  },
  "follow_up_suggestions": [
    "Would you like to know more about...",
    "Are you interested in..."
  ]
}
```

### 2. **POST /memory/context** - LSTM Memory Retrieval
Retrieve memories using LSTM gates from Component 5.

**Request Body:**
```json
{
  "user_id": "string",
  "current_message": "string",
  "conversation_id": "string", 
  "max_memories": 10
}
```

**Response:**
```json
{
  "selected_memories": [
    {
      "content_summary": "Memory content...",
      "importance_score": 0.85,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ],
  "relevance_scores": [0.9, 0.8, 0.7],
  "token_usage": 150,
  "assembly_metadata": {
    "source": "component5_lstm",
    "total_memories": 5
  },
  "retrieval_time_ms": 200.5
}
```

### 3. **GET /health** - System Health Check
Check the health status of all components.

**Response:**
```json
{
  "overall_healthy": true,
  "component_health": {
    "component5": {
      "initialized": true,
      "memory_manager_healthy": true,
      "gate_network_healthy": true
    },
    "component6": {
      "conversation_manager": true,
      "gemini_client": true
    },
    "component7": {
      "quality_analyzer": true
    }
  },
  "system_metrics": {
    "total_conversations": 150,
    "avg_response_time_ms": 1200.5,
    "success_rate": 0.95
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### 4. **GET /performance** - Performance Metrics
Get comprehensive performance metrics.

**Response:**
```json
{
  "conversation_metrics": {
    "total_conversations": 150,
    "avg_response_time_ms": 1200.5,
    "success_rate": 0.95,
    "user_satisfaction_avg": 0.88
  },
  "component5_stats": {
    "memories_retrieved": 750,
    "context_assemblies": 150,
    "gate_decisions": 300,
    "errors": 2
  },
  "component6_stats": {
    "active_conversations": 5,
    "memory_cache_size": 100
  },
  "component7_stats": {
    "quality_analyses": 150,
    "avg_quality_score": 0.85
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

## 🔧 Utility Endpoints

### 5. **POST /conversation/batch** - Batch Processing
Process multiple conversations in batch.

**Request Body:**
```json
[
  {
    "user_id": "user1",
    "user_message": "Hello!",
    "conversation_id": "conv1"
  },
  {
    "user_id": "user2", 
    "user_message": "How are you?",
    "conversation_id": "conv2"
  }
]
```

### 6. **POST /test/integration** - Integration Test
Run the complete integration test suite.

**Response:**
```json
{
  "message": "Integration test started in background",
  "status": "running",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### 7. **GET /test/health** - Detailed Health Test
Comprehensive health check with detailed component status.

### 8. **POST /memory/retrieve** - Memory Retrieval
Direct memory retrieval using LSTM gates.

---

## 📊 Data Models

### EmotionalState
```json
{
  "primary_emotion": "string",     // e.g., "excited", "sad", "happy"
  "intensity": 0.8,                // 0.0 to 1.0
  "confidence": 0.9                // 0.0 to 1.0
}
```

### ConversationRequest
```json
{
  "user_id": "string",             // Required: Unique user identifier
  "user_message": "string",        // Required: User's message/query
  "conversation_id": "string",     // Required: Unique conversation identifier
  "emotional_state": {              // Optional: User's emotional state
    "primary_emotion": "excited",
    "intensity": 0.8,
    "confidence": 0.9
  },
  "max_memories": 10,              // Optional: Max memories to retrieve (1-50)
  "include_analysis": true         // Optional: Include response analysis
}
```

### ConversationResponse
```json
{
  "response_id": "string",
  "conversation_id": "string", 
  "user_id": "string",
  "enhanced_response": "string",
  "original_response": "string",   // Optional
  "processing_timestamp": "string",
  "processing_time_ms": 1500.5,
  "quality_metrics": {            // Optional
    "overall_quality": 0.85,
    "coherence_score": 0.9,
    "relevance_score": 0.8,
    "safety_score": 1.0
  },
  "safety_checks": {               // Optional
    "passed": true
  },
  "context_usage": {               // Optional
    "memories_referenced": 5,
    "context_integration_score": 0.8
  },
  "response_metadata": {           // Optional
    "fallback_used": false,
    "processing_time_ms": 1200.5
  },
  "follow_up_suggestions": [       // Optional
    "Would you like to know more?",
    "Are you interested in..."
  ],
  "proactive_suggestions": [],     // Optional
  "memory_context_metadata": {     // Optional
    "memories_used": 5,
    "retrieval_time_ms": 200.3
  },
  "enhancement_metadata": {        // Optional
    "fallback_used": false,
    "error": null
  }
}
```

---

## 🚀 Getting Started

### 1. Installation
```bash
# Install dependencies
pip install -r api_requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your AstraDB credentials
```

### 2. Environment Variables
```bash
# Required AstraDB Configuration
ASTRA_DB_API_ENDPOINT=https://your-endpoint.apps.astra.datastax.com
ASTRA_DB_TOKEN=AstraCS:your-token
KEYSPACE=memory_db

# Optional Gemini API Configuration  
GEMINI_API_KEY=your-gemini-api-key
```

### 3. Running the API
```bash
# Development mode
python fastapi_integration.py

# Production mode
uvicorn fastapi_integration:app --host 0.0.0.0 --port 8000
```

### 4. Access Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔄 Workflow Example

### Complete Conversation Processing

1. **User sends query**:
```bash
curl -X POST "http://localhost:8000/conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "user_message": "I am feeling excited about my new AI project!",
    "conversation_id": "conv001",
    "emotional_state": {
      "primary_emotion": "excited",
      "intensity": 0.8,
      "confidence": 0.9
    }
  }'
```

2. **API processes through workflow**:
   - LSTM Memory Retrieval (Component 5)
   - Context Assembly (Component 6)
   - Gemini AI Response Generation
   - Quality Analysis (Component 7)

3. **Response includes**:
   - Enhanced AI response
   - Memory context used
   - Quality metrics
   - Follow-up suggestions
   - Processing time

---

## 🛠️ Error Handling

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (invalid input)
- **500**: Internal Server Error
- **503**: Service Unavailable (components not initialized)

### Error Response Format
```json
{
  "error": "Error message",
  "error_type": "ExceptionType", 
  "timestamp": "2025-01-01T12:00:00Z",
  "traceback": "Optional traceback for debugging"
}
```

---

## 📈 Monitoring and Metrics

### Health Check
```bash
curl http://localhost:8000/health
```

### Performance Metrics
```bash
curl http://localhost:8000/performance
```

### Integration Testing
```bash
curl -X POST http://localhost:8000/test/integration
```

---

## 🔧 Development

### Running Tests
```bash
# Run integration tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_conversation.py
```

### API Testing
```bash
# Test conversation endpoint
curl -X POST "http://localhost:8000/conversation" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "user_message": "Hello", "conversation_id": "test"}'

# Test health
curl http://localhost:8000/health
```

---

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pydantic Documentation**: https://pydantic-docs.helpmanual.io/
- **Swagger UI**: http://localhost:8000/docs
- **Integration Test Suite**: `integration_main.py`

---

## 🎯 Key Features

✅ **Complete Workflow**: LSTM Memory → Context Assembly → Gemini AI Response  
✅ **Real-time Processing**: Async/await support for high performance  
✅ **Comprehensive Analytics**: Quality metrics, performance tracking  
✅ **Error Handling**: Robust error handling and logging  
✅ **Interactive Documentation**: Swagger UI and ReDoc  
✅ **Batch Processing**: Support for multiple conversations  
✅ **Health Monitoring**: Component health and performance metrics  
✅ **Integration Testing**: Built-in test suite execution  
✅ **Production Ready**: Proper lifecycle management and cleanup
