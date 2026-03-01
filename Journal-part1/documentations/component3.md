# Component 3: NER, Temporal & Sentence Embeddings

## Purpose
Provides advanced text understanding through named entity recognition, temporal pattern analysis, and high-quality semantic embeddings for memory management.

## Core Functions
- **Named Entity Recognition**: Extract people, locations, organizations using spaCy en_core_web_lg
- **Future Event Detection**: Identify upcoming events, deadlines, appointments with temporal parsing
- **Semantic Embeddings**: Generate high-quality sentence vectors using sentence-transformers
- **Temporal Analysis**: Extract time-based patterns and cyclical behaviors
- **Entity Relationships**: Map connections between people, places, and events

## Key Components

### Entity Extractor
- **Person Detection**: spaCy NER + relationship context (family, friends, colleagues)
- **Location Processing**: Geocoding and place disambiguation
- **Organization Recognition**: Company and institution identification
- **Custom Entities**: User-specific important people and places
- **Entity Linking**: Resolve name variations and disambiguate references

### Event Extractor
- **Temporal Parser**: Parse "tomorrow", "next Friday", "in 2 weeks" using dateutil
- **Event Classification**: Medical, professional, social, travel, personal tasks
- **Importance Scoring**: Rank events by significance and user patterns
- **Deadline Detection**: Identify time-sensitive commitments
- **Recurring Patterns**: Detect repeated events and schedules

### Embedding Generator
- **Primary Model**: all-mpnet-base-v2 for high-quality 768-dim embeddings
- **Lightweight Model**: all-MiniLM-L6-v2 for fast 384-dim comparisons
- **Batch Processing**: Efficient parallel embedding generation
- **Similarity Calculation**: Cosine similarity for semantic matching
- **Caching System**: LRU cache for frequently accessed embeddings

### Temporal Analyzer
- **Pattern Detection**: Daily, weekly, monthly, seasonal writing patterns
- **Anomaly Detection**: Unusual timing or frequency changes
- **Cycle Analysis**: Identify recurring behavioral patterns
- **Trend Analysis**: Long-term changes in writing habits

## Data Models
- **SemanticAnalysis**: entities, events, embeddings, temporal patterns, topics
- **PersonEntity**: name, relationship type, context clues, confidence
- **FutureEvent**: event text, predicted date, importance score, participants
- **TemporalFeatures**: time patterns, frequency metrics, anomaly scores

## Processing Pipeline
1. **Entity Extraction**: spaCy NER + custom pattern matching for people/places/organizations
2. **Event Detection**: Temporal expression parsing + event classification
3. **Embedding Generation**: Sentence transformer encoding with caching
4. **Relationship Mapping**: Connect entities based on co-occurrence and context
5. **Pattern Analysis**: Identify temporal and behavioral patterns

## Performance Targets
- **Accuracy**: 90% F1 for NER, 85% future event detection, 95% temporal parsing
- **Speed**: <300ms complete semantic analysis, <50ms embeddings
- **Quality**: 80% relationship detection precision, 90% temporal accuracy

## Technical Implementation
- **Models**: spaCy en_core_web_lg, sentence-transformers (mpnet/MiniLM)
- **Libraries**: dateutil for temporal parsing, numpy for similarity calculations
- **Caching**: 10k embedding cache, efficient batch processing
- **Memory**: <500MB for 1000 concurrent entries

## Output Features
- **Entity Lists**: People, places, organizations with confidence and relationships
- **Event Timeline**: Future events with dates, importance, and context
- **Embeddings**: Primary and lightweight semantic vectors for similarity
- **Temporal Patterns**: Writing habits, cycles, and anomalies
- **Relationship Graph**: Connections between entities and their contexts