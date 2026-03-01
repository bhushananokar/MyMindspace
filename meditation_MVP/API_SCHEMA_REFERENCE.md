# MeditationDB API Schema Documentation

Based on testing, here are the **exact** field requirements for the MeditationDB API:

## ✅ Working API Schemas

### 1. User Creation (`POST /api/users`)
```json
{
  "name": "string (required)",
  "email": "string (required)", 
  "preferences": {
    "experience_level": "beginner|intermediate|advanced",
    "preferred_duration": number,
    "favorite_meditations": ["string"],
    "goals": ["stress_reduction", "better_sleep", "focus", ...] // Must use exact values
  }
}
```

**Valid Goals Only:**
- stress_reduction
- better_sleep
- focus
- emotional_balance
- anxiety_relief
- pain_management
- spiritual_growth
- creativity
- self_awareness
- compassion
- patience
- mindful_eating

### 2. Session Creation (`POST /api/sessions`)
```json
{
  "user_id": "string (required)",
  "input_type": "audio|text (required)",
  "input_data": {} // Object (required)
}
```

**❌ NOT ALLOWED:**
- metadata (entire field rejected)
- meditation_type 
- status
- duration/session_duration

### 3. Feedback Creation (`POST /api/feedback`)
```json
{
  "user_id": "string (required)",
  "session_id": "string (required)", 
  "meditation_type": "string (required)",
  "rating": number // 1-5 (required)
}
```

**❌ NOT ALLOWED:**
- feedback_text
- comment
- categories (entire field rejected)

### 4. Vector Creation (`POST /api/vectors`)
```json
{
  "entity_id": "string (required)",
  "entity_type": "user|session|meditation|audio (required)",
  "embedding": [number] // 384-dimensional array (required),
  "metadata": {
    "dimension": number,
    "version": "string"
    // ❌ NOT ALLOWED: created_by, custom fields
  }
}
```

## 🔧 Integration Notes

### Error Handling
- API returns 400 for validation errors with detailed messages
- Errors include both field validation and value validation
- Response format: `{"success": false, "message": "...", "error": "ERROR_CODE"}`

### Response Format
- Successful operations return the created object with an `id` field
- Some endpoints may return `_id` instead of `id`
- Always check both field names when extracting IDs

### Connection Management
- Use aiohttp for async HTTP requests
- Ensure proper session cleanup to avoid "Unclosed client session" warnings
- Implement timeout handling (30 second default recommended)

### Field Validation
- API is very strict about allowed fields
- Extra/unknown fields are rejected with validation errors
- Required fields must be present and correctly typed
- Enum values (like goals) must match exactly

## 🚀 Migration Impact

### What Works Seamlessly
1. ✅ User CRUD operations
2. ✅ Session creation and retrieval  
3. ✅ Basic feedback submission
4. ✅ API health checks
5. ✅ Connection testing

### What Needs Adjustment
1. ⚠️ Meditation type tracking - must be handled separately
2. ⚠️ Session status updates - use dedicated endpoints
3. ⚠️ Rich feedback data - limited to rating only
4. ⚠️ Vector metadata - restricted fields only

### Recommended Approach
1. **Start Simple**: Use minimal required fields for initial integration
2. **Test Incrementally**: Add fields one by one to identify what's supported
3. **Handle Gracefully**: Wrap API calls in try/catch for validation errors
4. **Cache Metadata**: Store additional metadata locally if API doesn't support it
5. **Use Dedicated Endpoints**: Check if specific operations have dedicated endpoints

## 📋 Next Steps

1. **✅ Basic Integration Complete**: Users, sessions, feedback working
2. **🔄 Vector Operations**: Need to test vector similarity search
3. **🔍 Advanced Features**: Explore analytics and recommendation endpoints
4. **🛠️ Production Ready**: Add proper error handling, retries, logging
5. **📚 Documentation**: Update API documentation with exact schemas

## 🎯 Success Metrics

- ✅ User creation and retrieval: **Working**
- ✅ Session creation and retrieval: **Working** 
- ✅ Feedback submission: **Working**
- ⚠️ Vector operations: **Needs refinement**
- 🔄 Analytics integration: **Not yet tested**
- 🔄 Recommendation engine: **Not yet tested**

The core functionality for your meditation MVP is now successfully integrated with the MeditationDB API!