# Gemini Engine Components 5, 6 & 7

Production-ready AI conversational system with advanced LSTM memory integration, contextual understanding, and response analysis.

## 🚀 Quick Start

### Option 1: FastAPI Server (Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Gemini API key and AstraDB credentials

# Start the FastAPI server
python api_integration.py

# Access the API documentation
# Swagger UI: http://localhost:8007/docs
# ReDoc: http://localhost:8007/redoc
```

### Option 2: Direct Integration
```bash
# Run the complete integration
python gemini_engine_complete_integration.py

# Or run direct Component 6→7 integration
python component6_7_integration.py
```

## 📋 Overview

The Gemini Engine is a sophisticated AI conversational system that integrates LSTM memory management, contextual understanding, and response quality analysis. Components 5, 6, and 7 work together to deliver personalized, context-aware conversations with continuous improvement.

### Architecture Flow
```
LSTM Memory Gates (Comp 5) → Context Assembly (Comp 6) → Gemini API → Response Analysis (Comp 7)
     ↑                                                                        ↓
     ←←←←←←←←←←← Feedback Loop for Optimization ←←←←←←←←←←←←←←←←←←←←←←←←←
```

## 🌐 FastAPI Integration

### API Endpoints

The FastAPI server provides comprehensive REST API endpoints for the complete Gemini Engine workflow:

#### **Core Conversation Processing**
- **`POST /conversation`** - Complete conversation processing through LSTM Memory → Context Assembly → Gemini AI → Quality Analysis
- **`POST /conversation/batch`** - Batch processing of multiple conversations
- **`GET /health`** - System health check for all components
- **`GET /performance`** - Performance metrics for all components

#### **Memory Management**
- **`POST /memory/context`** - LSTM memory context retrieval using Component 5
- **`POST /memory/retrieve`** - Direct memory retrieval bypassing full workflow

#### **Testing & Diagnostics**
- **`POST /test/integration`** - Run complete integration test suite
- **`GET /test/health`** - Detailed health test with component diagnostics

### API Documentation

Once the server is running, access the interactive documentation:
- **Swagger UI**: `http://localhost:8007/docs`
- **ReDoc**: `http://localhost:8007/redoc`

### Example API Usage

#### Process a Conversation
```bash
curl -X POST "http://localhost:8007/conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "user_message": "I'\''m feeling excited about my new AI project!",
    "conversation_id": "conv_001",
    "emotional_state": {
      "primary_emotion": "excited",
      "intensity": 0.8,
      "confidence": 0.9
    }
  }'
```

#### Get Memory Context
```bash
curl -X POST "http://localhost:8007/memory/context" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "current_message": "How am I feeling about work lately?",
    "conversation_id": "conv_001",
    "max_memories": 10
  }'
```

#### Health Check
```bash
curl -X GET "http://localhost:8007/health"
```

## 🧠 Component 5: LSTM Memory Gates

**Purpose**: Intelligent memory management using LSTM-inspired gates for selective memory storage and retrieval.

### Core Features
- **Input Gate**: Decides which memories are important enough to store (40-60% storage rate)
- **Forget Gate**: Manages memory decay and deletion over time
- **Output Gate**: Filters memories for conversation relevance
- **Database Integration**: Uses AstraDB `memory_embeddings` collection
- **Feature Processing**: 90-dimensional feature vectors from Component 4
- **Embedding Support**: 768-dimensional text embeddings from Component 3

### Memory Types
- **Emotion**: Feelings, moods, emotional states
- **Event**: Appointments, meetings, scheduled activities
- **Insight**: Learning moments, realizations, discoveries
- **Conversation**: General interactions and thoughts

## 🏗️ Component 6: Gemini Brain Integration

**Purpose**: Complete conversational AI with intelligent context assembly and memory retrieval.

### Core Modules

#### `gemini_client.py`
- **Function**: Gemini API integration and response generation
- **Features**: Rate limiting, error handling, response validation
- **Token Limit**: 2000 tokens per request with smart budget management

#### `memory_retriever.py` 
- **Function**: Intelligent memory selection from Component 5 output
- **Features**: Relevance scoring, temporal weighting, context filtering
- **Input**: LSTM Memory Gates output with gate scores

#### `context_assembler.py`
- **Function**: Assembles retrieved memories into coherent context
- **Features**: Token budget optimization, relevance ranking, context formatting
- **Output**: Structured prompt ready for Gemini consumption

#### `conversation_manager.py`
- **Function**: Coordinates dialogue flow and conversation state
- **Features**: Turn management, context continuity, conversation history
- **Capabilities**: Multi-turn conversations, context preservation

#### `personality_engine.py`
- **Function**: Adapts responses to user personality and preferences
- **Features**: Communication style matching, humor preference, formality adjustment
- **Supported Styles**: Formal, Casual, Professional, Friendly, Humorous, Direct, Elaborate

#### `proactive_engine.py`
- **Function**: Initiates contextually appropriate conversations
- **Features**: Engagement timing, topic suggestions, follow-up generation
- **Use Cases**: Check-ins, event reminders, relationship building

#### `response_processor.py`
- **Function**: Post-processes Gemini responses for optimization
- **Features**: Quality validation, formatting, personalization injection

### Key Features

- **Memory Integration**: Seamlessly uses LSTM Memory Gates output
- **Context Optimization**: Smart token budget management under 2000 limit
- **Personality Adaptation**: Matches user communication preferences
- **Proactive Engagement**: Initiates meaningful conversations
- **Quality Assurance**: Response validation and optimization
- **Error Resilience**: Comprehensive error handling and fallbacks

## 🔍 Component 7: Gemini Response Analysis

**Purpose**: Response quality monitoring, user satisfaction tracking, and continuous improvement.

### Core Modules

#### `quality_analyzer.py`
- **Function**: Comprehensive response quality assessment
- **Metrics**: Coherence, relevance, helpfulness, accuracy
- **Scoring**: 0-1 scale with detailed breakdowns

#### `metrics_collector.py`
- **Function**: Collects and aggregates conversation metrics
- **Tracks**: Response times, success rates, quality trends
- **Storage**: Time-series data for performance analysis

#### `feedback_engine.py`
- **Function**: User feedback collection and processing
- **Types**: Explicit ratings, implicit signals, behavioral feedback
- **Integration**: Real-time feedback incorporation

#### Response Analysis Pipeline
1. **Quality Scoring**: Multi-dimensional response evaluation
2. **Context Effectiveness**: Analysis of memory usage and relevance
3. **User Satisfaction**: Prediction and tracking
4. **Improvement Suggestions**: Actionable optimization recommendations
5. **Feedback Loop**: Continuous system refinement

### Analysis Metrics

- **Quality Scores**: Overall quality, coherence, relevance, helpfulness
- **Context Usage**: Memory utilization, relevance scores, token efficiency
- **User Satisfaction**: Predicted and actual satisfaction ratings
- **Performance**: Response times, success rates, conversation effectiveness

## 🔧 Configuration

### Environment Variables

```bash
# Gemini API Configuration (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro
GEMINI_MAX_TOKENS=2000
GEMINI_TEMPERATURE=0.7

# AstraDB Configuration (REQUIRED)
ASTRA_DB_API_ENDPOINT=your_astra_endpoint_here
ASTRA_DB_TOKEN=your_astra_token_here
KEYSPACE=memory_db

# Component Integration
ENABLE_MEMORY_GATES=true
ENABLE_PROACTIVE_ENGINE=true
ENABLE_RESPONSE_ANALYSIS=true

# Performance Settings
MAX_CONCURRENT_REQUESTS=10
RESPONSE_TIMEOUT_SECONDS=30
MEMORY_CACHE_SIZE=1000

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/gemini_engine.log
```

### User Profile Configuration

```python
user_profile = UserProfile(
    user_id="user_001",
    communication_style=CommunicationStyle.FRIENDLY,
    preferred_response_length="moderate",  # short, moderate, long
    emotional_matching=True,
    humor_preference=0.7,  # 0.0 to 1.0
    formality_level=0.3,   # 0.0 to 1.0
    conversation_depth=0.8  # 0.0 to 1.0
)
```

## 📊 Usage Examples

### FastAPI Server Usage

#### Start the Server
```bash
# Start the FastAPI server
python api_integration.py

# Server will be available at:
# - API: http://localhost:8007
# - Swagger UI: http://localhost:8007/docs
# - ReDoc: http://localhost:8007/redoc
```

#### Python Client Example
```python
import requests
import json

# Process a conversation
response = requests.post("http://localhost:8007/conversation", json={
    "user_id": "user_001",
    "user_message": "How was your day?",
    "conversation_id": "conv_123",
    "emotional_state": {
        "primary_emotion": "happy",
        "intensity": 0.7,
        "confidence": 0.9
    }
})

result = response.json()
print(f"AI Response: {result['enhanced_response']}")
print(f"Quality Score: {result.get('quality_metrics', {}).get('overall_quality', 'N/A')}")
```

### Direct Integration Usage

#### Basic Conversation Processing
```python
from gemini_engine_orchestrator import GeminiEngineOrchestrator

# Initialize orchestrator
orchestrator = GeminiEngineOrchestrator()

# Process user input
response = await orchestrator.process_conversation(
    user_id="user_001",
    user_input="How was your day?",
    conversation_id="conv_123"
)

print(f"AI Response: {response.content}")
print(f"Quality Score: {response.quality_score}")
```

### Advanced Integration with Memory

```python
# Process with specific memory context
memory_context = MemoryContext(
    selected_memories=[...],
    relevance_scores=[0.9, 0.7, 0.5],
    token_usage=150,
    assembly_metadata={"context_type": "emotional_support"}
)

response = await orchestrator.process_conversation_with_context(
    user_id="user_001",
    user_input="I'm feeling anxious about tomorrow's presentation",
    memory_context=memory_context
)
```

### Response Analysis

```python
# Analyze response quality
analysis = await orchestrator.analyze_response(
    conversation_id="conv_123",
    response_id="resp_456"
)

print(f"Quality Metrics: {analysis.quality_scores}")
print(f"User Satisfaction: {analysis.user_satisfaction}")
print(f"Improvements: {analysis.improvement_suggestions}")
```

## 🧪 Testing

### FastAPI Testing
```bash
# Start the server
python api_integration.py

# Test API endpoints using curl or Postman
curl -X GET "http://localhost:8007/health"
curl -X POST "http://localhost:8007/test/integration"
```

### Unit Tests
```bash
# Run Component 5 tests
pytest tests/component5/ -v

# Run Component 6 tests
pytest tests/component6/ -v

# Run Component 7 tests  
pytest tests/component7/ -v

# Run integration tests
pytest tests/integration/ -v
```

### Integration Testing
```bash
# Test complete pipeline
python integration_main.py

# Test Component 6→7 direct integration
python test_component6_7_integration.py
```

### Performance Benchmarks
```bash
# Run performance tests
python benchmarks/performance_test.py

# Generate performance report
python benchmarks/generate_report.py
```

## 📈 Performance Metrics

### Component 5 (LSTM Memory) Metrics
- **Gate Inference**: <100ms per memory
- **Memory Creation**: <200ms including database save
- **Context Assembly**: <500ms for 1000+ memories
- **Storage Efficiency**: 40-60% storage rate vs traditional systems
- **Memory Relevance**: >0.7 average relevance score

### Component 6 Metrics
- **Response Time**: Target <2 seconds average
- **Context Assembly**: <500ms for memory retrieval and assembly
- **Token Efficiency**: 85%+ token utilization under budget
- **Memory Relevance**: >0.7 average relevance score

### Component 7 Metrics
- **Analysis Speed**: <100ms for response analysis
- **Quality Prediction**: 90%+ correlation with human ratings
- **Satisfaction Tracking**: Real-time user satisfaction monitoring
- **Improvement ROI**: Measurable quality improvements over time

### FastAPI Server Metrics
- **API Response Time**: <3 seconds for complete conversation processing
- **Memory Retrieval**: <1 second for LSTM memory context
- **Health Check**: <500ms for system diagnostics
- **Concurrent Requests**: Supports multiple simultaneous conversations

## 🚨 Monitoring & Alerts

### Health Checks
- **API Connectivity**: Gemini API availability
- **AstraDB Connection**: Database connectivity and performance
- **Memory Integration**: Component 5 LSTM interface health  
- **Response Quality**: Quality threshold monitoring
- **Performance**: Response time and error rate tracking
- **FastAPI Server**: Server health and component initialization

### Alerting
- **API Failures**: Immediate notification for Gemini API issues
- **Database Issues**: AstraDB connection and performance alerts
- **Quality Degradation**: Alerts when quality drops below thresholds
- **Performance Issues**: Response time or error rate spikes
- **Memory Issues**: Component 5 LSTM integration problems
- **Server Issues**: FastAPI server health and component failures

## 🔐 Security & Privacy

### Data Protection
- **User Data**: Encrypted storage and transmission
- **Memory Content**: Secure handling of personal information
- **API Keys**: Environment-based secure storage
- **Conversation Logs**: Configurable retention policies

### Access Control
- **User Authentication**: Secure user identification
- **API Rate Limiting**: Prevents abuse and ensures fair usage
- **Data Anonymization**: Privacy-preserving analytics
- **Audit Logging**: Comprehensive activity tracking

## 🛠️ Troubleshooting

### Common Issues

#### FastAPI Server Issues
```bash
# Check if server is running
curl -X GET "http://localhost:8007/health"

# Check server logs
python api_integration.py

# Test all endpoints
curl -X GET "http://localhost:8007/"
curl -X GET "http://localhost:8007/health"
curl -X GET "http://localhost:8007/performance"
```

#### Gemini API Connection Issues
```bash
# Check API key configuration
python -c "from config.settings import settings; print(settings.GEMINI_API_KEY[:10] + '...')"

# Test API connectivity
python scripts/test_gemini_connection.py

# Test via FastAPI
curl -X POST "http://localhost:8007/conversation" -H "Content-Type: application/json" -d '{"user_id":"test","user_message":"test","conversation_id":"test"}'
```

#### AstraDB Connection Issues
```bash
# Check database configuration
python -c "import os; print('ASTRA_DB_API_ENDPOINT:', os.getenv('ASTRA_DB_API_ENDPOINT', 'NOT_SET'))"

# Test database connectivity
python scripts/test_astra_connection.py

# Test via FastAPI
curl -X POST "http://localhost:8007/memory/context" -H "Content-Type: application/json" -d '{"user_id":"test","current_message":"test","conversation_id":"test"}'
```

#### Memory Integration Problems
```bash
# Verify Component 5 interface
python scripts/test_memory_interface.py

# Check memory retrieval
python scripts/debug_memory_retrieval.py

# Test LSTM memory via FastAPI
curl -X POST "http://localhost:8007/memory/retrieve" -H "Content-Type: application/json" -d '{"user_id":"test","current_message":"test","conversation_id":"test"}'
```

#### Performance Issues
```bash
# Profile response times
python scripts/profile_performance.py

# Analyze bottlenecks
python scripts/analyze_bottlenecks.py
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python gemini_engine_orchestrator.py --debug --verbose
```

## 📚 API Reference

### FastAPI Endpoints

#### Core Endpoints

**`POST /conversation`**
- **Purpose**: Complete conversation processing through LSTM Memory → Context Assembly → Gemini AI → Quality Analysis
- **Request Body**: `ConversationRequest` with user_id, user_message, conversation_id, emotional_state
- **Response**: `ConversationResponse` with enhanced_response, quality_metrics, processing_time_ms

**`POST /memory/context`**
- **Purpose**: LSTM memory context retrieval using Component 5
- **Request Body**: `MemoryContextRequest` with user_id, current_message, conversation_id, max_memories
- **Response**: `MemoryContextResponse` with selected_memories, relevance_scores, token_usage

**`GET /health`**
- **Purpose**: System health check for all components
- **Response**: `HealthCheckResponse` with overall_healthy, component_health, system_metrics

**`GET /performance`**
- **Purpose**: Performance metrics for all components
- **Response**: `PerformanceResponse` with conversation_metrics, component5_stats, component6_stats, component7_stats

#### Testing Endpoints

**`POST /test/integration`**
- **Purpose**: Run complete integration test suite
- **Response**: Status message with test execution details

**`GET /test/health`**
- **Purpose**: Detailed health test with component diagnostics
- **Response**: Comprehensive system health and performance diagnostics

### Direct Integration API

#### GeminiEngineOrchestrator

**`async process_conversation(user_id, user_input, conversation_id=None)`**
- Processes user input through complete pipeline
- Returns: `EnhancedResponse` with AI response and metadata

**`async analyze_response(conversation_id, response_id)`**
- Analyzes response quality and effectiveness  
- Returns: `ResponseAnalysis` with metrics and suggestions

**`async health_check()`**
- Comprehensive system health verification
- Returns: `Dict` with component statuses

**`async get_conversation_metrics(conversation_id)`**
- Retrieves conversation performance metrics
- Returns: `ConversationMetrics` object

### Response Objects

#### EnhancedResponse
```python
@dataclass
class EnhancedResponse:
    response_id: str
    conversation_id: str
    user_id: str
    content: str
    quality_score: float
    context_used: List[str]
    processing_time_ms: float
    metadata: Dict[str, Any]
```

#### ResponseAnalysis
```python
@dataclass  
class ResponseAnalysis:
    analysis_id: str
    response_id: str
    conversation_id: str
    user_id: str
    quality_scores: Dict[str, float]
    context_usage: Dict[str, Any]
    user_satisfaction: float
    improvement_suggestions: List[str]
```



