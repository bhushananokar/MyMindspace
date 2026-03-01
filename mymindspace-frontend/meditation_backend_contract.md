# Meditation Backend API Contract

Python/FastAPI service providing AI-powered meditation recommendations, audio analysis, and TTS script generation.

## Tech Stack

- **Backend**: Python / FastAPI
- **AI**: Google Gemini (`gemini-flash-latest`) for script generation
- **ML**: Rule-based + ML pipeline for text recommendations
- **Audio**: Custom MFCC-based audio encoder for emotion/VAD analysis
- **Storage**: MeditationDB API (external — see `meditation_backend_contract.md`)
- **File Storage**: Firebase Storage (audio uploads)
- **Deployment**: Local / Docker

## Base URL

```
http://localhost:8000
```

## Authentication

None required (MVP). All endpoints are open.

## Response Format

Successful responses return the model fields directly (no envelope).

Error responses:
```json
{ "error": "error_type", "message": "Human-readable message", "detail": "..." }
```
`detail` is only included when `DEBUG=true`.

---

## Enum Reference

| Field | Valid Values |
|---|---|
| `preferences.experience_level` | `beginner` `intermediate` `advanced` |
| `preferences.goals` | `stress_reduction` `better_sleep` `focus` `emotional_balance` `anxiety_relief` `pain_management` `spiritual_growth` `creativity` `self_awareness` `compassion` `patience` `mindful_eating` |
| `preferences.favorite_meditations` | `mindfulness` `breathing` `body_scan` `loving_kindness` `walking` `guided_imagery` `mantra` `zen` `vipassana` `transcendental` `movement` `sound_bath` |
| `session.status` | `pending` `processing` `completed` `failed` |
| `rating` | `1` `2` `3` `4` `5` |
| `duration_minutes` | `1`–`30` |

---

## Endpoints

### Health & Info

#### `GET /`

Health check.

**Response `200`:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-28T10:00:00Z",
  "version": "1.0.0"
}
```

---

#### `GET /stats`

System statistics pulled from MeditationDB.

**Response `200`:** Raw analytics object from MeditationDB API.

**Errors:**
- `500` — database query failed

---

### Users — `/api/users`

#### `POST /api/users`

Create a new user.

**Required fields:** `name`

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "preferences": {
    "experience_level": "beginner",
    "preferred_duration": 10,
    "favorite_meditations": ["mindfulness", "breathing"],
    "goals": ["stress_reduction", "better_sleep"]
  }
}
```

**Response `200`:**
```json
{
  "user_id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "preferences": { ... },
  "created_at": "2026-02-28T10:00:00Z"
}
```

**Errors:**
- `500` — creation or retrieval failed

---

#### `GET /api/users/{user_id}`

Get user profile by ID.

**Response `200`:**
```json
{
  "user_id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "preferences": { ... },
  "created_at": "2026-02-28T10:00:00Z"
}
```

**Errors:**
- `404` — user not found

---

#### `PUT /api/users/{user_id}/preferences`

Update user preferences.

**Request:** Any valid preferences fields (freeform dict forwarded to MeditationDB).

```json
{
  "experience_level": "intermediate",
  "preferred_duration": 15,
  "goals": ["focus", "self_awareness"]
}
```

**Response `200`:**
```json
{ "message": "Preferences updated successfully" }
```

**Errors:**
- `500` — update failed

---

### Recommendations — `/api/recommend`

#### `POST /api/recommend`

Get meditation recommendations from a diary entry.

Runs the text analysis pipeline then optionally enhances results with vector-similarity personalization.

**Required fields:** `diary_text` · `user_id`

**Request:**
```json
{
  "diary_text": "Feeling stressed about work deadlines and having trouble sleeping",
  "user_id": "user_123"
}
```

**Response `200`:**
```json
{
  "session_id": "uuid",
  "recommendations": [
    {
      "meditation_type": "breathing",
      "confidence": 0.92,
      "rationale": "Recommended for stress and anxiety relief",
      "source": "text_analysis"
    }
  ],
  "status": "completed",
  "method": "text_analysis_with_personalization"
}
```

**Notes:**
- `method` is `text_analysis` when personalization fails, `text_analysis_with_personalization` when it succeeds.
- A session is automatically created and stored in MeditationDB.

**Errors:**
- `500` — recommendation pipeline failed

---

#### `POST /api/enhance`

Get enhanced recommendations combining text analysis and a previously processed audio session.

If `session_id` is omitted, falls back to text-only recommendations (same as `POST /api/recommend`).

**Query params:** `session_id` (optional)

**Request body:** Same as `POST /api/recommend`.

```json
{
  "diary_text": "Feeling anxious about tomorrow",
  "user_id": "user_123"
}
```

**Response `200`:** Same schema as `POST /api/recommend`.

`method` will be `multimodal_with_personalization` or `text_analysis_with_personalization` depending on path taken.

**Errors:**
- `400` — audio session not yet completed
- `500` — pipeline failed

---

### Scripts — `/api/generate-script`

#### `POST /api/generate-script`

Generate a TTS-ready meditation script using Gemini.

**Required fields:** `meditation_type` · `user_id`

**Optional fields:** `duration_minutes` (default `5`, range `1`–`30`)

**Request:**
```json
{
  "meditation_type": "mindfulness",
  "user_id": "user_123",
  "duration_minutes": 8
}
```

**Response `200`:**
```json
{
  "meditation_type": "mindfulness",
  "instructions": "Focus on present moment awareness...",
  "script": "Welcome to your mindfulness practice. Find a comfortable position...",
  "duration_minutes": "8",
  "format": "TTS-ready"
}
```

**Errors:**
- `503` — Gemini API not configured (`GEMINI_API_KEY` missing or invalid)
- `500` — script generation failed

**Notes:**
- Requires `GEMINI_API_KEY` environment variable.
- No fallback — returns 503 if Gemini is unavailable.
- Model: `gemini-flash-latest`

---

### Audio — `/api/analyze`

#### `POST /api/analyze`

Upload an audio file for emotion and VAD analysis. Processing is performed synchronously.

**Content-Type:** `multipart/form-data`

**Form fields:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | file | yes | Audio file |
| `user_id` | string | yes | User ID |
| `session_id` | string | no | Existing session ID to associate |

**Supported formats:** `wav` `mp3` `m4a` `ogg` `flac`

**Response `200`:**
```json
{
  "session_id": "uuid",
  "audio_url": "https://storage.googleapis.com/bucket/audio/session_id.wav",
  "status": "processing",
  "message": "Audio uploaded successfully. Processing in background."
}
```

**Errors:**
- `400` — `user_id` not provided
- `500` — upload or analysis failed

**Notes:**
- Audio is uploaded to Firebase Storage.
- MFCC features extracted locally; audio embedding is always 384-dimensional (padded with zeros if needed).
- Emotion labels map to: `calm` · `neutral` · `stressed`.
- Use `GET /api/sessions/{session_id}/results` to retrieve full analysis output.

---

### Sessions — `/api/sessions`

#### `GET /api/sessions/{session_id}/status`

Get the current processing status of a session.

**Response `200`:**
```json
{
  "session_id": "uuid",
  "status": "completed",
  "created_at": "2026-02-28T10:00:00Z",
  "has_results": true
}
```

**`status` values:** `pending` · `processing` · `completed` · `failed`

**Errors:**
- `404` — session not found
- `500` — status retrieval failed

---

#### `GET /api/sessions/{session_id}/results`

Get the full results for a completed session.

**Response `200`:**
```json
{
  "session_id": "uuid",
  "status": "completed",
  "results": {
    "audio_analysis": {
      "features": {
        "emotion": { "label": "stressed", "probs": [0.2, 0.3, 0.5] },
        "vad": { "speech_ratio": 0.65, "segment_count": 4 }
      },
      "embeddings": {
        "audio": [ 384 floats ],
        "emotion": [0.2, 0.3, 0.5]
      }
    },
    "method": "audio_processing"
  },
  "audio_url": "https://storage.googleapis.com/bucket/audio/session_id.wav"
}
```

**Errors:**
- `404` — session not found
- `500` — retrieval failed

---

### Feedback — `/api/feedback`

#### `POST /api/feedback`

Submit user feedback for a meditation session.

**Required fields:** `user_id` · `session_id` · `meditation_type` · `rating` (1–5)

**Request:**
```json
{
  "user_id": "user_123",
  "session_id": "uuid",
  "meditation_type": "mindfulness",
  "rating": 4,
  "comment": "Really helpful for reducing anxiety"
}
```

**Response `200`:**
```json
{
  "feedback_id": "uuid",
  "message": "Feedback recorded successfully"
}
```

**Notes:**
- Submitting feedback triggers an async background update of the user's vector embedding.
- Embedding update failure is logged but does not fail the request.

**Errors:**
- `500` — feedback save failed

---

### Vectors — `/api/vectors`

#### `GET /api/users/{user_id}/similar`

Find users with similar behavior/preference vectors.

**Query params:** `limit` (default `5`)

**Response `200`:**
```json
{
  "user_id": "user_123",
  "similar_users": [ ... ]
}
```

**Errors:**
- `500` — similarity search failed

---

#### `POST /api/vectors/create-user`

Create or refresh a user's vector embedding from their history and feedback.

**Query params:** `user_id` (required)

**Response `200`:**
```json
{
  "message": "User embedding created",
  "vector_id": "uuid"
}
```

**Errors:**
- `500` — embedding creation failed

---

### Development (DEBUG only)

These endpoints are only registered when `DEBUG=true` in the environment.

#### `GET /dev/test-recommendation`

Run a test recommendation with a hardcoded diary text (`"Feeling stressed and anxious about work"`).

**Response:** Same as `POST /api/recommend`.

---

#### `GET /dev/meditation-types`

List all meditation types loaded from the local meditation dataset.

**Response `200`:**
```json
{
  "meditation_types": ["Mindfulness Meditation", "Breathing Meditation", ...],
  "count": 12
}
```

---

## Error Reference

| HTTP | Condition |
|---|---|
| `400` | Missing required field (e.g. `user_id` for audio upload) |
| `400` | Audio session not yet completed when calling `/api/enhance` |
| `404` | User or session not found in MeditationDB |
| `500` | Internal pipeline failure — check server logs |
| `502` | MeditationDB upstream error (non-5xx class) |
| `503` | Gemini API not configured / MeditationDB temporarily unavailable (cold start) |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (for scripts) | Google Gemini API key |
| `FIREBASE_PROJECT_ID` | Yes (for audio) | Firebase project ID |
| `FIREBASE_STORAGE_BUCKET` | Yes (for audio) | Firebase Storage bucket name |
| `DEBUG` | No | Set to `true` to enable debug endpoints and error details |

---

## Audio Analysis Notes

The local audio encoder produces a **127-dimensional** feature vector (6×20 MFCC stats + 7 global scalars). This is zero-padded to **384 dimensions** before being stored in MeditationDB to satisfy the vector schema requirement. The extra 257 dimensions carry no information.

Emotion inference is heuristic-only (calm / neutral / stressed) based on energy variability and spectral brightness — not a trained classifier.
