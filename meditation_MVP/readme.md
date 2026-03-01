# Meditation Recommendation API

AI-powered meditation recommendations with multimodal analysis, personalized suggestions, and TTS-ready script generation.

## Features

- **Text-based Recommendations**: Analyze diary entries and emotional states to suggest appropriate meditations
- **Audio Processing**: Upload voice recordings for emotion detection and enhanced recommendations  
- **Script Generation**: Generate TTS-ready meditation scripts using AI (Gemini API)
- **User Learning**: Collect feedback to improve future recommendations
- **Vector Similarity**: Find similar users and personalize suggestions based on success patterns
- **Multimodal Analysis**: Combine text and audio inputs for comprehensive emotional assessment

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: Firebase Firestore
- **Audio Processing**: librosa, NumPy (MFCC feature extraction)
- **AI Integration**: Google Gemini API for script generation
- **Vector Operations**: In-memory NumPy operations for similarity search

## Quick Start

### Prerequisites

- Python 3.11+
- Firebase project with Firestore enabled
- Google Gemini API key (optional, for script generation)

### Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd meditation_MVP
pip install -r requirements.txt
```

2. **Firebase Setup**:
   - Create Firebase project at https://console.firebase.google.com/
   - Enable Firestore Database
   - Download service account key as `firebase_config.json`
   - Place in project root directory

3. **Environment Setup**:
```bash
# Add your Gemini API key to api/meditation_service.py
# Replace: genai.configure(api_key="YOUR_KEY_HERE")
```

### Running the Server

```bash
python main.py --debug
```

Server starts at: http://localhost:8000

## API Documentation

### Authentication
None required for MVP (production should implement proper auth)

### Base URL
```
http://localhost:8000
```

---

## Endpoints

### Health & System

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00.000000",
  "version": "1.0.0"
}
```

#### `GET /stats`
System statistics and usage metrics.

---

### User Management

#### `POST /api/users`
Create a new user.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "preferences": {
    "experience_level": "beginner",
    "preferred_duration": 10
  }
}
```

**Response:**
```json
{
  "user_id": "user_123",
  "name": "John Doe",
  "email": "john@example.com",
  "preferences": {...},
  "created_at": "2024-01-01T10:00:00Z"
}
```

#### `GET /api/users/{user_id}`
Get user profile and preferences.

#### `PUT /api/users/{user_id}/preferences`
Update user preferences.

---

### Meditation Recommendations

#### `POST /api/recommend`
Get meditation recommendations based on text input.

**Request Body:**
```json
{
  "diary_text": "Feeling stressed about work deadlines and having trouble sleeping",
  "user_id": "test_user_123"
}
```

**Response:**
```json
{
  "session_id": "session_456",
  "recommendations": [
    {
      "meditation_type": "Body Scan Meditation",
      "confidence": 0.92,
      "rationale": "Recommended for stress relief",
      "source": "rule_based"
    }
  ],
  "status": "completed",
  "method": "text_analysis"
}
```

#### `POST /api/generate-script`
Generate TTS-ready meditation script.

**Request Body:**
```json
{
  "meditation_type": "Mindfulness Meditation",
  "user_id": "test_user_123",
  "duration_minutes": 5
}
```

**Response:**
```json
{
  "meditation_type": "Mindfulness Meditation",
  "instructions": "Focus on present moment awareness",
  "script": "Welcome to your mindfulness practice...",
  "duration_minutes": "5-7",
  "format": "TTS-ready"
}
```

---

### Audio Processing

#### `POST /api/analyze`
Upload and analyze audio file for emotion detection.

**Parameters:**
- `user_id` (query): User ID
- `file` (form-data): Audio file (.wav, .mp3, .m4a, .flac)

**Response:**
```json
{
  "session_id": "session_789",
  "status": "completed", 
  "message": "Audio processed successfully",
  "results": {
    "audio_analysis": {...},
    "file_info": {...}
  }
}
```

#### `GET /api/sessions/{session_id}/status`
Check processing status for audio session.

#### `GET /api/sessions/{session_id}/results`
Get detailed audio analysis results.

#### `POST /api/enhance`
Get enhanced recommendations combining text and audio analysis.

**Query Parameters:**
- `session_id`: Audio session ID

**Request Body:**
```json
{
  "diary_text": "Feeling anxious today",
  "user_id": "test_user_123"
}
```

**Response:**
```json
{
  "session_id": "session_101",
  "recommendations": [...],
  "method": "text_audio_combined",
  "audio_insights": {
    "emotional_state": "stressed",
    "stress_indicators": ["high_stress_voice_patterns"],
    "voice_energy": "high"
  }
}
```

---

### Feedback & Learning

#### `POST /api/feedback`
Submit user feedback to improve recommendations.

**Request Body:**
```json
{
  "user_id": "test_user_123",
  "session_id": "session_456",
  "meditation_type": "Mindfulness Meditation",
  "rating": 4,
  "comment": "Very helpful for stress relief"
}
```

**Response:**
```json
{
  "feedback_id": "feedback_789",
  "message": "Feedback recorded successfully"
}
```

---

### Vector Similarity & Personalization

#### `GET /api/users/{user_id}/similar`
Find users with similar meditation preferences and success patterns.

**Query Parameters:**
- `limit` (optional): Number of similar users to return (default: 5)

**Response:**
```json
{
  "user_id": "test_user_123",
  "similar_users": [
    {
      "user_id": "user_456",
      "similarity": 0.85,
      "success_rate": 0.92,
      "metadata": {...}
    }
  ]
}
```

#### `POST /api/vectors/create-user`
Create or update user embedding vector for personalization.

**Query Parameters:**
- `user_id`: User ID

---

## Error Handling

All endpoints return structured error responses:

```json
{
  "error": "validation_error",
  "message": "Invalid input data",
  "detail": "Additional error details"
}
```

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable

---

## Data Flow

### 1. Text-only Recommendation
```
User Input → Text Analysis → Rule-based Selection → Recommendations
```

### 2. Audio-enhanced Recommendation  
```
Audio Upload → MFCC Extraction → Emotion Detection → 
Text Analysis → Combined Analysis → Enhanced Recommendations
```

### 3. Personalized Recommendation
```
User History → Vector Embedding → Similarity Search → 
Base Recommendations → Personalization → Final Recommendations
```

### 4. Learning Loop
```
User Feedback → Preference Updates → Vector Updates → 
Improved Future Recommendations
```

---

## Database Schema (Firestore)

### Collections

#### `users`
```json
{
  "id": "user_123",
  "name": "John Doe", 
  "email": "john@example.com",
  "preferences": {
    "experience_level": "beginner",
    "preferred_duration": 10,
    "favorite_meditations": ["mindfulness"]
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### `sessions`
```json
{
  "id": "session_456",
  "user_id": "user_123",
  "status": "completed",
  "input_type": "text|audio|multimodal",
  "input_data": {...},
  "results": {...},
  "created_at": "timestamp"
}
```

#### `feedback`
```json
{
  "id": "feedback_789",
  "user_id": "user_123",
  "session_id": "session_456",
  "meditation_type": "Mindfulness Meditation",
  "rating": 4,
  "comment": "Very helpful",
  "created_at": "timestamp"
}
```

#### `vectors`
```json
{
  "id": "vector_101",
  "entity_id": "user_123",
  "entity_type": "user|session|meditation",
  "embedding": [0.1, 0.2, ...],
  "metadata": {...},
  "created_at": "timestamp"
}
```

---

## Development

### Adding New Meditation Types

1. Update `Core_engine/meditation.csv`
2. Add rules in `Core_engine/meditation_selector.py`
3. Test with `/api/recommend`

### Adding New Audio Features

1. Extend `preprocessing_unit/audio_preprocessor.py`
2. Update `Encoders/audio_encoder.py`
3. Modify emotion detection logic

### Customizing Recommendations

1. Modify rules in `api/meditation_service.py`
2. Update vector similarity weights
3. Adjust confidence scoring

---

## Deployment

### Production Checklist

- [ ] Set up production Firebase project
- [ ] Configure environment variables
- [ ] Enable Firebase security rules
- [ ] Set up proper authentication
- [ ] Configure CORS for your domain
- [ ] Add rate limiting
- [ ] Set up monitoring and logging
- [ ] Configure backup procedures

### Environment Variables

```bash
FIREBASE_PROJECT_ID=your-project-id
GEMINI_API_KEY=your-gemini-key
DEBUG=false
```

---

## Limitations & Future Enhancements

### Current Limitations
- No authentication (MVP only)
- In-memory vector operations (doesn't scale beyond thousands of users)
- Basic emotion detection
- English language only

### Planned Enhancements
- User authentication & authorization
- Advanced ML models for emotion detection
- Multi-language support
- Real-time collaboration features
- Mobile app integration
- Advanced analytics dashboard

---

## Support

For technical issues or questions:
1. Check server logs for error details
2. Verify Firebase configuration
3. Test individual endpoints with Postman
4. Check audio file format compatibility

---
