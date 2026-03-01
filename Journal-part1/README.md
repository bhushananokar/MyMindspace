# AI Journal Analysis Pipeline: Components 2, 3, and 4 + AstraDB Integration

**Production-Ready Emotion Analysis, NER & Temporal Processing, Feature Engineering, and Multi-Database Storage Pipeline**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![AstraDB](https://img.shields.io/badge/Database-AstraDB-purple.svg)](https://astra.datastax.com)
[![Vector Search](https://img.shields.io/badge/Features-Vector%20Search-green.svg)](https://github.com)
[![Event Storage](https://img.shields.io/badge/Events-Temporal%20DB-orange.svg)](https://github.com)
[![Tests](https://img.shields.io/badge/Tests-Passing-green.svg)](https://github.com)

## 🎯 **Overview**

This repository contains a production-ready integration of three AI components that work together to analyze journal entries and store them across multiple databases:

- **Component 2**: Emotion Analysis with Reinforcement Learning
- **Component 3**: Named Entity Recognition & Temporal Analysis  
- **Component 4**: Feature Engineering Pipeline
- **AstraDB Integration**: Vector database storage with semantic search capabilities
- **Temporal Database**: Event storage and follow-up question generation
- **Journal CRUD API Integration**: Real-time journal entry retrieval and processing

The pipeline transforms natural language journal entries into structured data optimized for **vector operations**, **semantic similarity search**, and **temporal event tracking**. It can now retrieve and process journal entries directly from the database instead of using hardcoded examples.

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# Set up your .env file with database credentials
ASTRA_DB_APPLICATION_TOKEN=your_application_token_here
ASTRA_DB_API_ENDPOINT=https://your-database-id-your-region.apps.astra.datastax.com
ASTRA_DB_KEYSPACE=your_keyspace_name

# Journal CRUD API endpoint (required for database integration)
JOURNAL_CRUD_ENDPOINT=https://journal-crud-service-222233295505.asia-south1.run.app

# Optional: Temporal database for event storage
TEMPORAL_DB_ENDPOINT=https://your-temporal-db-endpoint.com/api/events

# Optional: Direct collection endpoints (alternative to AstraDB)
CHAT_EMBEDDINGS_COLLECTION_ENDPOINT=https://your-chat-embeddings-endpoint.com
SEMANTIC_SEARCH_COLLECTION_ENDPOINT=https://your-semantic-search-endpoint.com
```

### **Installation**
```bash
git clone <repository-url>
cd comp_2_3_4_integration
pip install -r requirements.txt
pip install astrapy python-dotenv requests
```

### **Run Integration**

#### **Process Journal Entries from Database**
```python
from integration_main import AstraDBIntegrator

# Initialize integrator (automatically connects to databases)
integrator = AstraDBIntegrator()

# Process user's journal entries from database
results = integrator.process_user_journals_from_db(
    user_id="ninad",  # Replace with actual user ID
    limit=5,  # Process up to 5 entries
    push_to_astra=True
)

if results:
    print(f"✅ Successfully processed {len(results)} journal entries")
    for result in results:
        print(f"📊 Chat embeddings ID: {result.chat_embeddings['id']}")
        print(f"🔍 Semantic search ID: {result.semantic_search['id']}")
```

#### **Process Specific Journal Entry**
```python
# Process a specific journal entry by ID
result = integrator.process_specific_journal_from_db(
    journal_id="7NvPnsdh5qvkGb8S0DJA",  # Replace with actual journal ID
    push_to_astra=True
)

if result:
    print("✅ Successfully processed journal entry")
    print(f"📊 Processing time: {result.processing_time_ms:.1f}ms")
```

#### **Fallback: Process Hardcoded Example**
```python
# Process hardcoded journal entry (original functionality)
result = integrator.process_journal_entry(
    text="Had a great breakthrough at work today! Meeting with Sarah tomorrow at 2 PM.",
    user_id="user_123",
    session_id="session_456"
)

# Push to AstraDB collections
success = integrator.push_to_astra_db(result)
if success:
    print("✅ Data successfully pushed to AstraDB!")
    print(f"📊 Chat embeddings ID: {result.chat_embeddings['id']}")
    print(f"🔍 Semantic search ID: {result.semantic_search['id']}")
```

### **Run Tests**
```bash
python integration_main.py
```

## 📊 **Database Collections Schema**

### **Collection 1: `chat_embeddings`**
**Purpose**: Real-time conversation analysis and chat context storage

```json
{
  "id": "uuid",
  "user_id": "string",
  "entry_id": "uuid",
  "message_content": "text",
  "message_type": "user_message|ai_response|system_message",
  "timestamp": "ISO8601 with Z suffix",
  "session_id": "uuid",
  "conversation_context": "string",
  "primary_embedding": [768 dimensions - float array],
  "lightweight_embedding": [384 dimensions - float array],
  "text_length": "integer",
  "processing_time_ms": "float",
  "model_version": "string",
  "semantic_tags": ["array of strings"],
  "emotion_context": "JSON string",
  "entities_mentioned": "JSON string",
  "temporal_context": "JSON string",
  "feature_vector": [90 dimensions - float array],
  "temporal_features": [25 dimensions - float array],
  "emotional_features": [20 dimensions - float array],
  "semantic_features": [30 dimensions - float array],
  "user_features": [15 dimensions - float array],
  "feature_completeness": "float",
  "confidence_score": "float"
}
```

### **Collection 2: `semantic_search`**
**Purpose**: Content discovery and relationship mapping for semantic search

```json
{
  "id": "uuid",
  "user_id": "string",
  "content_type": "journal_entry|event|person|location|topic",
  "title": "string",
  "content": "text",
  "primary_embedding": [768 dimensions - float array],
  "created_at": "ISO8601 with Z suffix",
  "updated_at": "ISO8601 with Z suffix",
  "tags": ["array of strings"],
  "linked_entities": "JSON string",
  "search_metadata": "JSON string",
  "feature_vector": [90 dimensions - float array],
  "temporal_features": [25 dimensions - float array],
  "emotional_features": [20 dimensions - float array],
  "semantic_features": [30 dimensions - float array],
  "user_features": [15 dimensions - float array]
}
```

### **Collection 3: `temporal_events`**
**Purpose**: Event storage and follow-up question generation

```json
{
  "event_id": "string",
  "user_id": "string",
  "event_text": "string",
  "event_type": "professional|medical|social|personal",
  "event_subtype": "string",
  "parsed_date": "ISO8601",
  "original_date_text": "string",
  "participants": ["array of strings"],
  "location": "string",
  "importance_score": "float",
  "confidence": "float",
  "emotional_context": "JSON string",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

## 🏗️ **Architecture**

### **Component 2: Emotion Analysis**
- **Technology**: Cardiff NLP RoBERTa + Reinforcement Learning (SAC)
- **Features**: Real-time learning, user personalization, 8 emotion categories
- **Output**: Emotion analysis with confidence scores
- **Database Integration**: Stores emotion context as JSON in `chat_embeddings`

### **Component 3: NER & Temporal Analysis**
- **Technology**: spaCy NER + Temporal parsing + Sentence-Transformers
- **Features**: Entity extraction, temporal event detection, semantic embeddings
- **Output**: Structured semantic analysis with 768D and 384D embeddings
- **Database Integration**: Primary source of vector embeddings + event extraction

### **Component 4: Feature Engineering**
- **Technology**: Production feature extraction and normalization
- **Features**: 90D vectors (25+20+30+15), quality control, validation
- **Output**: Structured features with metadata
- **Database Integration**: Provides feature vectors and quality metrics

### **Multi-Database Integration Layer**
- **AstraDB**: Vector database for semantic search and embeddings
- **Temporal Database**: Event storage and follow-up question generation
- **Journal CRUD API**: Real-time journal entry retrieval and processing
- **HTTP Endpoints**: Direct collection endpoints as alternative
- **Connection Management**: Automatic database connection via environment variables
- **Data Formatting**: Strict schema compliance with proper data types
- **Error Handling**: Robust fallbacks and local file backup

## 📁 **Repository Structure**

```
├── comp2/                          # Component 2: Emotion Analysis
│   ├── src/                       # Core emotion analysis modules
│   │   ├── emotion_analyzer.py    # Main emotion analysis engine
│   │   ├── base_emotion_detector.py
│   │   ├── experience_buffer.py
│   │   ├── policy_network.py
│   │   ├── reward_calculator.py
│   │   └── rl_trainer.py
│   ├── models/                    # Pre-trained emotion models
│   ├── data/                      # Data schemas and user data
│   └── tests/                     # Unit tests
├── comp3/                         # Component 3: NER & Temporal
│   ├── src/                       # NER and temporal analysis modules
│   │   ├── analyzer.py            # Main semantic analysis engine
│   │   ├── embedding_generator.py # Vector embeddings (768D, 384D)
│   │   ├── entity_extractor.py    # NER for people, locations, orgs
│   │   ├── event_extractor.py     # Temporal event extraction
│   │   ├── psychological_analyzer.py
│   │   └── temporal_analyzer.py   # Time-based analysis
│   ├── data/                      # Event patterns and schemas
│   └── tests/                     # Unit tests
├── comp4/                         # Component 4: Feature Engineering
│   ├── src/                       # Feature engineering modules
│   │   ├── processor.py           # Main feature processor
│   │   ├── feature_engineer.py    # 90D feature vector generation
│   │   ├── emotional_extractor.py # 20D emotional features
│   │   ├── semantic_extractor.py  # 30D semantic features
│   │   ├── temporal_extractor.py  # 25D temporal features
│   │   ├── user_extractor.py      # 15D user features
│   │   └── quality_controller.py  # Quality validation
│   ├── data/                      # Data schemas and structures
│   └── tests/                     # Unit tests
├── integration_main.py            # Main integration file
├── requirements.txt               # Core dependencies
├── requirements_astra.txt         # AstraDB-specific dependencies
├── tests/                         # Integration and production tests
├── documentations/                # Detailed component documentation
└── run_tests.py                   # Test runner script
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required for AstraDB connection
export ASTRA_DB_APPLICATION_TOKEN="your_application_token_here"
export ASTRA_DB_API_ENDPOINT="https://your-database-id-your-region.apps.astra.datastax.com"
export ASTRA_DB_KEYSPACE="your_keyspace_name"

# Required for Journal CRUD API integration
export JOURNAL_CRUD_ENDPOINT="https://journal-crud-service-222233295505.asia-south1.run.app"

# Optional: Temporal database for event storage
export TEMPORAL_DB_ENDPOINT="https://your-temporal-db-endpoint.com/api/events"

# Optional: Direct collection endpoints (alternative to AstraDB)
export CHAT_EMBEDDINGS_COLLECTION_ENDPOINT="https://your-chat-embeddings-endpoint.com"
export SEMANTIC_SEARCH_COLLECTION_ENDPOINT="https://your-semantic-search-endpoint.com"
```

### **Database Setup**

#### **Journal CRUD API Integration**
The system integrates with a Journal CRUD API to retrieve and process real journal entries from the database.

**API Endpoints Used:**
- `GET /api/journals/user/:userId` - Get journals by user ID (supports pagination)
- `GET /api/journals/:id` - Get journal by ID
- `GET /api/journals/user/:userId/search?q=query` - Search journals by title, content, or tags

**Journal Entry Schema:**
```json
{
  "id": "auto-generated-firestore-id",
  "userId": "string (required)",
  "title": "string (required, 1-200 chars)",
  "content": "string (required, min 1 char)",
  "mood": "string (optional: happy|sad|anxious|calm|excited|angry|neutral)",
  "tags": ["array", "of", "strings"],
  "createdAt": "2025-08-27T10:30:00.000Z",
  "updatedAt": "2025-08-27T10:30:00.000Z"
}
```

**Features:**
- Automatic UUID generation for user IDs and entry IDs
- Firestore timestamp format handling
- Real-time journal entry processing
- Batch processing with pagination support
- Search functionality for content discovery

#### **AstraDB Collections**
```sql
-- Create collections in AstraDB
CREATE COLLECTION chat_embeddings;
CREATE COLLECTION semantic_search;

-- Enable vector search (if using AstraDB Vector)
ALTER COLLECTION chat_embeddings ADD VECTOR primary_embedding DIMENSION 768;
ALTER COLLECTION chat_embeddings ADD VECTOR lightweight_embedding DIMENSION 384;
ALTER COLLECTION semantic_search ADD VECTOR primary_embedding DIMENSION 768;
```

#### **Temporal Database Schema**
```sql
-- Create events table
CREATE TABLE temporal_events (
    event_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    event_text TEXT,
    event_type VARCHAR,
    event_subtype VARCHAR,
    parsed_date TIMESTAMP,
    original_date_text VARCHAR,
    participants JSON,
    location VARCHAR,
    importance_score FLOAT,
    confidence FLOAT,
    emotional_context JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📈 **Performance & Features**

### **Vector Search Capabilities**
- **Primary Embeddings**: 768D high-quality vectors for semantic similarity
- **Lightweight Embeddings**: 384D fast vectors for quick search operations
- **Feature Vectors**: 90D comprehensive feature representation
- **Real-time Processing**: <500ms end-to-end pipeline execution

### **Event Processing**
- **Temporal Extraction**: Automatic detection of future events
- **Follow-up Questions**: Intelligent question generation for events
- **Event Classification**: Professional, medical, social, personal categories
- **Importance Scoring**: Automatic event importance assessment

### **Search Operations**
```python
# Vector similarity search in AstraDB
similar_entries = chat_collection.find(
    {"primary_embedding": {"$vector": query_embedding, "$similarity": 0.8}}
)

# Semantic search across content types
search_results = search_collection.find(
    {"tags": {"$in": ["work", "meeting"]}}
)

# Event-based queries
upcoming_events = temporal_db.query(
    "SELECT * FROM temporal_events WHERE parsed_date > NOW() AND user_id = ?",
    [user_id]
)
```

### **Quality Metrics**
- **Feature Completeness**: >90% target
- **Confidence Scores**: >85% target
- **Embedding Accuracy**: Exact dimension matching (768D, 384D, 90D)
- **Schema Compliance**: 100% field name and type accuracy
- **Event Detection**: >80% accuracy for temporal events

## 🧪 **Testing & Validation**

### **Schema Compliance Testing**
```python
# Test output format compliance
result = integrator.process_journal_entry(
    text="Test entry for validation",
    user_id="test_user"
)

# Verify schema compliance
assert len(result.chat_embeddings["primary_embedding"]) == 768
assert len(result.chat_embeddings["lightweight_embedding"]) == 384
assert len(result.chat_embeddings["feature_vector"]) == 90
```

### **Database Connection Testing**
```python
# Test AstraDB connectivity
integrator = AstraDBIntegrator()
print("✅ AstraDB connection successful!")

# Test data insertion
success = integrator.push_to_astra_db(result)
assert success == True

# Test event extraction
events = integrator.event_extractor.extract_events(
    "Meeting tomorrow at 2 PM with Sarah"
)
assert len(events) > 0
```

## 🚀 **Production Deployment**

### **Prerequisites**
- Python 3.8+
- 4GB+ RAM recommended
- AstraDB account with Vector enabled
- Valid application token and API endpoint
- Optional: Temporal database for event storage

### **Docker Deployment**
```dockerfile
FROM python:3.8-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install astrapy python-dotenv requests
CMD ["python", "integration_main.py"]
```

### **Monitoring & Health Checks**
```python
# Check component health
integrator = AstraDBIntegrator()

# Verify database connections
if integrator.astra_connector.db:
    print("✅ AstraDB: Connected")
else:
    print("❌ AstraDB: Connection failed")

# Check event extraction
events = integrator.event_extractor.extract_events("Test event tomorrow")
print(f"✅ Event extraction: {len(events)} events found")
```

## 🔍 **Use Cases**

### **Real-time Journal Analysis**
- **Emotion Tracking**: Monitor user emotional patterns over time
- **Entity Recognition**: Track people, locations, and organizations mentioned
- **Temporal Analysis**: Understand writing patterns and seasonal trends
- **Event Scheduling**: Automatic detection and storage of future events

### **Semantic Search & Discovery**
- **Content Recommendation**: Find similar journal entries
- **Relationship Mapping**: Discover connections between people and events
- **Topic Clustering**: Group related content for insights
- **Event Follow-up**: Generate intelligent questions for upcoming events

### **AI Training & Research**
- **Feature Engineering**: 90D vectors for machine learning models
- **Vector Database**: Optimized storage for similarity search
- **Metadata Enrichment**: Rich context for AI model training
- **Temporal Modeling**: Event-based prediction and analysis

## 🛡️ **Security & Best Practices**

### **Database Security**
- **Application Tokens**: Read-only by default, scope-limited access
- **API Endpoints**: HTTPS encrypted connections
- **Keyspace Isolation**: Prevents cross-tenant data access
- **Environment Variables**: Never commit credentials to version control

### **Data Privacy**
- **User Isolation**: Strict user_id separation
- **Session Management**: UUID-based session tracking
- **Audit Logging**: Complete processing history tracking
- **Event Privacy**: Secure storage of personal events and schedules

## 📚 **Complete API Reference**

### **AstraDBIntegrator Class**
```python
class AstraDBIntegrator:
    def __init__(self, config_path: str = "unified_config.yaml")
    def process_journal_entry(
        text: str,
        user_id: str,
        session_id: str = None,
        entry_timestamp: datetime = None,
        entry_id: str = None,
        message_type: str = "user_message",
        user_history: Optional[UserHistoryContext] = None
    ) -> AstraDBOutput
    def process_user_journals_from_db(
        user_id: str,
        limit: int = 10,
        offset: int = 0,
        push_to_astra: bool = True
    ) -> List[AstraDBOutput]
    def process_specific_journal_from_db(
        journal_id: str,
        push_to_astra: bool = True
    ) -> Optional[AstraDBOutput]
    def push_to_astra_db(output: AstraDBOutput) -> bool
    def batch_process(entries: List[Dict]) -> List[AstraDBOutput]
    def export_for_astra_db(output: AstraDBOutput) -> Dict
```

### **AstraDBConnector Class**
```python
class AstraDBConnector:
    def __init__(self)  # Auto-connects via environment variables
    def push_to_collection(collection_name: str, data: Dict) -> bool
    def get_collection(collection_name: str) -> Collection
```

### **JournalCRUDClient Class**
```python
class JournalCRUDClient:
    def __init__(self)  # Auto-connects to Journal CRUD API
    def get_user_journals(user_id: str, limit: int = 10, offset: int = 0) -> List[Dict]
    def get_journal_by_id(journal_id: str) -> Optional[Dict]
    def search_user_journals(user_id: str, query: str, limit: int = 10) -> List[Dict]
```

### **EventExtractor Class**
```python
class EventExtractor:
    def __init__(self)
    def extract_events(text: str, reference_date: datetime = None) -> List[ExtractedEvent]
    def generate_followup_questions(events: List[ExtractedEvent], reference_date: datetime = None) -> List[FollowupQuestion]
    def store_events_to_db(events: List[ExtractedEvent], user_id: str, db_endpoint: str) -> Dict
    def extract_and_store_events(text: str, user_id: str, reference_date: datetime = None, db_endpoint: str = None) -> Dict
```

### **Component APIs**

#### **Component 2: Emotion Analysis**
```python
class EmotionAnalyzer:
    def analyze_emotion(text: str, user_id: str) -> EmotionAnalysis
    def get_emotion_scores(text: str) -> EmotionScores
    def update_user_baseline(user_id: str, emotion_data: Dict)
```

#### **Component 3: Semantic Analysis**
```python
class Component3Analyzer:
    def analyze(processed_text: str, user_id: str, entry_timestamp: datetime) -> SemanticAnalysis
    def extract_entities(text: str) -> List[Entity]
    def generate_embeddings(text: str) -> Embeddings
```

#### **Component 4: Feature Engineering**
```python
class Component4Processor:
    def process_journal_entry(
        emotion_analysis: EmotionAnalysis,
        semantic_analysis: SemanticAnalysis,
        user_id: str,
        entry_id: str,
        session_id: str,
        entry_timestamp: datetime,
        raw_text: str,
        user_history: Optional[UserHistoryContext] = None
    ) -> EngineeredFeatures
```

## 💡 **Usage Examples**

### **Process Journal Entries from Database**
```python
from integration_main import AstraDBIntegrator

# Initialize
integrator = AstraDBIntegrator()

# Process user's journal entries from database
results = integrator.process_user_journals_from_db(
    user_id="ninad",  # Replace with actual user ID
    limit=5,  # Process up to 5 entries
    push_to_astra=True
)

if results:
    print(f"✅ Successfully processed {len(results)} journal entries")
    for result in results:
        print(f"📊 Processing time: {result.processing_time_ms:.1f}ms")
        print(f"📊 Chat embeddings ID: {result.chat_embeddings['id']}")
        print(f"🔍 Semantic search ID: {result.semantic_search['id']}")
```

### **Process Specific Journal Entry**
```python
# Process a specific journal entry by ID
result = integrator.process_specific_journal_from_db(
    journal_id="7NvPnsdh5qvkGb8S0DJA",  # Replace with actual journal ID
    push_to_astra=True
)

if result:
    print("✅ Successfully processed journal entry")
    print(f"📊 Processing time: {result.processing_time_ms:.1f}ms")
```

### **Search and Process Journal Entries**
```python
# Search for specific entries
search_results = integrator.journal_client.search_user_journals(
    user_id="ninad",
    query="work",
    limit=3
)

# Process search results
for entry in search_results:
    result = integrator.process_specific_journal_from_db(
        journal_id=entry["id"],
        push_to_astra=True
    )
    if result:
        print(f"Processed: {entry.get('title', 'Untitled')}")
```

### **Fallback: Process Hardcoded Entry**
```python
# Process hardcoded journal entry (original functionality)
result = integrator.process_journal_entry(
    text="Had an amazing meeting with Sarah today! We discussed the new project and I'm feeling really excited about it. Meeting with the team tomorrow at 2 PM.",
    user_id="user_123",
    session_id="session_456"
)

# Push to databases
success = integrator.push_to_astra_db(result)
print(f"Success: {success}")
```

### **Batch Processing**
```python
# Process multiple entries
entries = [
    {"text": "Great day at work!", "user_id": "user_123"},
    {"text": "Feeling stressed about deadline", "user_id": "user_123"},
    {"text": "Wonderful dinner with family tomorrow", "user_id": "user_456"}
]

results = integrator.batch_process(entries)

# Push all to databases
for result in results:
    integrator.push_to_astra_db(result)
```

### **Event Extraction and Follow-up**
```python
# Extract events from text
events = integrator.event_extractor.extract_events(
    "Meeting with Sarah tomorrow at 2 PM. Doctor appointment next Friday."
)

# Generate follow-up questions
followups = integrator.event_extractor.generate_followup_questions(events)

# Store events to temporal database
storage_result = integrator.event_extractor.extract_and_store_events(
    text="Meeting with Sarah tomorrow at 2 PM",
    user_id="user_123"
)
```

### **Vector Search Operations**
```python
# Get embeddings for search
result = integrator.process_journal_entry(
    text="Looking for similar work-related entries",
    user_id="user_123"
)

# Use embeddings for similarity search
query_embedding = result.chat_embeddings["primary_embedding"]

# Search in AstraDB
similar_entries = integrator.astra_connector.get_collection("chat_embeddings").find(
    {"primary_embedding": {"$vector": query_embedding, "$similarity": 0.8}}
)
```

### **Feature Analysis**
```python
# Get comprehensive feature analysis
result = integrator.process_journal_entry(
    text="Complex emotional and temporal content",
    user_id="user_123"
)

# Access different feature dimensions
temporal_features = result.chat_embeddings["temporal_features"]  # 25D
emotional_features = result.chat_embeddings["emotional_features"]  # 20D
semantic_features = result.chat_embeddings["semantic_features"]  # 30D
user_features = result.chat_embeddings["user_features"]  # 15D

# Quality metrics
completeness = result.chat_embeddings["feature_completeness"]
confidence = result.chat_embeddings["confidence_score"]
```

## 🤝 **Contributing**

### **Development Setup**
```bash
git clone <repository-url>
cd comp_2_3_4_integration
pip install -r requirements.txt
pip install astrapy python-dotenv requests

# Set up .env file with your database credentials
# Run integration test
python integration_main.py
```

### **Code Quality Standards**
- All tests must pass before merging
- Database schema compliance validation
- Proper error handling and logging
- Performance benchmarks must be met
- Event extraction accuracy validation

## 📋 **Changelog**

### **v2.2.0 - Journal CRUD API Integration Release**
- ✅ Journal CRUD API integration for real-time journal entry processing
- ✅ Automatic UUID generation for user IDs and entry IDs
- ✅ Firestore timestamp format handling
- ✅ Batch processing with pagination support
- ✅ Search functionality for content discovery
- ✅ Enhanced error handling for API failures
- ✅ Backward compatibility with hardcoded examples
- ✅ Real-time journal entry retrieval and processing

### **v2.1.0 - Multi-Database Integration Release**
- ✅ Complete Components 2+3+4 + Multi-database integration
- ✅ AstraDB collections: `chat_embeddings` and `semantic_search`
- ✅ Temporal database integration for event storage
- ✅ Event extraction and follow-up question generation
- ✅ Vector search capabilities with 768D and 384D embeddings
- ✅ 90-dimensional feature vectors with quality metrics
- ✅ Automatic database connection management
- ✅ Schema compliance validation
- ✅ Production-ready error handling and backup

### **v2.0.0 - AstraDB Integration Release**
- ✅ Complete Components 2+3+4 + AstraDB integration
- ✅ Two optimized collections: `chat_embeddings` and `semantic_search`
- ✅ Vector search capabilities with 768D and 384D embeddings
- ✅ 90-dimensional feature vectors with quality metrics
- ✅ Automatic AstraDB connection management
- ✅ Schema compliance validation
- ✅ Production-ready error handling and backup

## 📄 **License**

[License information]

## 🆘 **Support**

For integration support and technical questions:
- Create an issue in this repository
- Review the documentation in `documentations/`
- Test database connections: `python integration_main.py`
- Check schema compliance in the output files
- Verify event extraction functionality

---

**🎉 Ready for Multi-Database Production Deployment!**

This pipeline is production-ready with full multi-database integration, vector search capabilities, temporal event processing, and comprehensive feature engineering for real-world AI applications.
