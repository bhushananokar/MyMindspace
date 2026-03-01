# MeditationDB API Migration Guide

## Overview
This document outlines the migration from Firebase Firestore to the MeditationDB API endpoint.

## ✅ Completed Changes

### 1. New API Client (`database/api_client.py`)
- **Purpose**: HTTP client for communicating with MeditationDB API
- **Features**: 
  - Complete CRUD operations for users, sessions, feedback, vectors, history
  - Analytics and health check endpoints
  - Proper error handling and connection management
  - 384-dimensional vector similarity search

### 2. API Collections Wrapper (`database/api_collections.py`) 
- **Purpose**: Maintains compatibility with existing code while using new API
- **Features**:
  - Drop-in replacement for Firebase collections
  - Maps Firebase operations to MeditationDB API calls
  - Preserves existing function signatures for minimal code changes

### 3. Updated Data Models (`api/models.py`)
- **Added**: New models aligned with MeditationDB API schema
  - `APIUserCreate`, `APIUserPreferences`
  - `APISessionCreate`, `APIFeedbackCreate`
  - `APIVectorCreate`, `APIHistoryCreate`
  - `APIResponse` for standardized responses

### 4. Service Layer Updates
- **meditation_service.py**: Updated import to use `api_collections`
- **audio_service.py**: Updated import to use `api_collections`
- **vector_service.py**: Updated import and function names

### 5. Configuration Updates (`config.py`)
- **Removed**: All Firebase-related configuration
- **Added**: MeditationDB API endpoint configuration
- **New Settings**:
  ```python
  MEDITATIONDB_API_URL = "https://meditationdb-api-222233295505.asia-south1.run.app"
  MEDITATIONDB_API_TIMEOUT = 30
  ```

### 6. Dependencies (`requirements_mvp.txt`)
- **Removed**: 
  - `firebase-admin`
  - `google-cloud-firestore`
  - `google-cloud-storage`
- **Added**:
  - `aiohttp>=3.8.0` (for HTTP requests)
  - `httpx>=0.24.0` (alternative HTTP client)

### 7. Main Application Updates (`main.py`)
- **Startup**: API connection test instead of Firebase initialization
- **Shutdown**: Proper cleanup of HTTP connections
- **Function Updates**: Analytics functions now use API endpoints

## 🔄 API Endpoint Mapping

| Firebase Operation | MeditationDB API Endpoint | Method |
|-------------------|---------------------------|---------|
| `users` collection | `/api/users` | POST/GET/PUT/PATCH |
| `sessions` collection | `/api/sessions` | POST/GET/PUT/PATCH |
| `feedback` collection | `/api/feedback` | POST/GET |
| `vectors` collection | `/api/vectors` | POST/GET |
| `history` collection | `/api/history` | POST/GET |
| Analytics | `/api/analytics/*` | GET |

## 📊 Data Schema Alignment

### Users
```javascript
// Firebase Schema
{
  id: string,
  name: string,
  email: string,
  preferences: {...},
  created_at: timestamp
}

// MeditationDB API Schema
{
  name: string,
  email: string,
  preferences: {
    experience_level: "beginner|intermediate|advanced",
    preferred_duration: number,
    favorite_meditations: string[],
    goals: string[]
  }
}
```

### Sessions
```javascript
// Firebase Schema
{
  id: string,
  user_id: string,
  status: string,
  input_type: string,
  input_data: {...},
  results: {...}
}

// MeditationDB API Schema
{
  user_id: string,
  input_type: "audio|text",
  input_data: {...},
  metadata: {
    meditation_type: string,
    session_duration: number
  }
}
```

### Feedback
```javascript
// Firebase Schema
{
  user_id: string,
  session_id: string,
  rating: number,
  comment: string
}

// MeditationDB API Schema
{
  user_id: string,
  session_id: string,
  rating: number,
  feedback_text: string,
  categories: {
    effectiveness: number,
    ease_of_use: number
  }
}
```

## 🚀 Getting Started

### 1. Install New Dependencies
```bash
pip install -r requirements_mvp.txt
```

### 2. Test API Connection
```bash
python test_api_integration.py
```

### 3. Environment Variables (Optional)
```bash
export MEDITATIONDB_API_URL="https://meditationdb-api-222233295505.asia-south1.run.app"
export MEDITATIONDB_API_TIMEOUT="30"
```

### 4. Start Application
```bash
python main.py
```

## 🔧 Key Benefits

1. **No Database Management**: External API handles all database operations
2. **Built-in Vector Search**: 384-dimensional similarity search included
3. **Comprehensive Analytics**: Rich analytics and insights endpoints
4. **Scalability**: Cloud-hosted API with built-in scaling
5. **Reduced Dependencies**: No Firebase SDK required

## 🛠️ Migration Notes

### Backward Compatibility
- All existing endpoints remain unchanged
- Function signatures preserved where possible
- Gradual migration approach - old Firebase files still exist

### Error Handling
- HTTP errors are caught and converted to appropriate exceptions
- Network timeouts and retries handled automatically
- Fallback behavior for API unavailability

### Performance Considerations
- HTTP requests may have higher latency than direct database calls
- Consider caching for frequently accessed data
- Batch operations where possible

### Testing
- `test_api_integration.py` provides comprehensive test coverage
- Tests all major operations: users, sessions, feedback, vectors
- Includes health checks and error scenarios

## 📁 File Structure After Migration

```
meditation_MVP/
├── database/
│   ├── api_client.py          # New: HTTP client for MeditationDB API
│   ├── api_collections.py     # New: Collections using API
│   ├── firebase_client.py     # Deprecated: Keep for reference
│   └── collections.py         # Deprecated: Keep for reference
├── api/
│   ├── models.py              # Updated: Added API-aligned models
│   ├── meditation_service.py  # Updated: Uses api_collections
│   ├── audio_service.py       # Updated: Uses api_collections
│   └── vector_service.py      # Updated: Uses api_collections
├── config.py                  # Updated: API configuration
├── main.py                    # Updated: API initialization
├── requirements_mvp.txt       # Updated: New dependencies
└── test_api_integration.py    # New: Integration tests
```

## 🎯 Next Steps

1. **Test the Integration**: Run the test script to verify all operations
2. **Monitor Performance**: Check API response times in production
3. **Update Documentation**: Reflect API changes in user documentation
4. **Remove Firebase Files**: Once confident, remove deprecated Firebase files
5. **Implement Caching**: Consider Redis or in-memory caching for performance

## ⚠️ Important Notes

- The MeditationDB API requires internet connectivity
- API rate limiting may apply (check API documentation)
- Ensure proper error handling for network issues
- Consider implementing retry logic for critical operations
- Monitor API health and usage metrics