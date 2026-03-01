# Journal Response & Retrieval Service — API Contract

> **Base URL**: `http://localhost:8001`
> **Version**: 1.0.0
> **Auth**: None (internal microservice — secure with auth proxy in production)
> **Framework**: FastAPI (Python)
> **CORS**: All origins allowed (`*`) — restrict in production

---

## Overview

HTTP-based Journal Response & Retrieval microservice. Accepts a processed journal entry context (from Journal Part 1) and returns a therapy-mode-aware AI response, relevant memory retrievals, and content recommendations. Powered by **GPT-4** for response generation, **Pinecone** for semantic retrieval, **Redis** for short-term context, and **PostgreSQL** for long-term memory persistence.

### Key Characteristics
- Therapy mode: **auto-selected** (CBT · DBT · ACT) based on emotion vectors
- Response latency: **sub-500ms** end-to-end (typical)
- Context window: **last 5 sessions** (short-term Redis) + **top-3 semantic matches** (Pinecone)
- Throughput: **1,000+ requests/hour**
- Content recommendations: **YouTube + Google Custom Search** (real-time, query built from emotion vectors)

---

## Data Models

### EmotionVector
| Field | Type | Description |
|-------|------|-------------|
| `joy` | float (0–1) | Joy intensity |
| `sadness` | float (0–1) | Sadness intensity |
| `anger` | float (0–1) | Anger intensity |
| `fear` | float (0–1) | Fear intensity |
| `surprise` | float (0–1) | Surprise intensity |
| `disgust` | float (0–1) | Disgust intensity |
| `trust` | float (0–1) | Trust intensity |
| `anticipation` | float (0–1) | Anticipation intensity |

### MemoryRecord
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string (UUID) | Source session identifier |
| `timestamp` | string (ISO 8601) | When this memory was stored |
| `summary` | string | Short summary of the past entry |
| `relevance_score` | float (0–1) | Cosine similarity to current entry |
| `therapy_mode` | string | `CBT` · `DBT` · `ACT` |

### ContentRecommendation
| Field | Type | Description |
|-------|------|-------------|
| `source` | string | `youtube` · `article` |
| `title` | string | Content title |
| `url` | string | Direct link |
| `relevance_reason` | string | Why this was recommended |

---

## Standard Response Envelopes

**Success**
```json
{ "status": "success", "data": { } }
```

**Error**
```json
{ "status": "error", "error": "Error description", "detail": "Details" }
```

---

---

## HTTP Endpoints

---

### `GET /`
**Summary**: Service info and endpoint discovery.

**Success Response** `200`
```json
{
  "service": "Journal Response & Retrieval Service",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "generate": "/journal/generate",
    "history": "/journal/history/{user_id}",
    "insights": "/journal/insights/{user_id}",
    "docs": "/docs"
  }
}
```

**Error Responses**
| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### `GET /health`
**Summary**: Liveness check. Verifies all downstream connections (Redis, PostgreSQL, Pinecone, GPT-4).

**Success Response** `200`
```json
{
  "status": "healthy",
  "services": {
    "redis": "connected",
    "postgres": "connected",
    "pinecone": "connected",
    "gpt4": "reachable"
  },
  "configuration": {
    "therapy_mode_auto": true,
    "short_term_window": 5,
    "top_k_retrieval": 3,
    "max_response_tokens": 512
  }
}
```

| Response Field | Type | Description |
|----------------|------|-------------|
| `status` | string | `healthy` · `degraded` · `unhealthy` |
| `services.redis` | string | `connected` · `disconnected` |
| `services.pinecone` | string | `connected` · `disconnected` |
| `services.gpt4` | string | `reachable` · `unreachable` |

**Error Responses**
| Status | Description |
|--------|-------------|
| 500 | One or more critical services unreachable |

> **Frontend usage**: Poll before first journal interaction in a session. If `status` is not `healthy`, show a service degraded banner.

---

### `POST /journal/generate`
**Summary**: Core endpoint. Accepts a processed journal entry and returns an AI therapy response with memory context and content recommendations.

**Request Body**
```json
{
  "user_id": "usr_abc123",
  "session_id": "sess_xyz789",
  "entry_text": "I've been feeling overwhelmed at work lately...",
  "emotion_vector": {
    "joy": 0.1,
    "sadness": 0.6,
    "anger": 0.2,
    "fear": 0.4,
    "surprise": 0.0,
    "disgust": 0.1,
    "trust": 0.2,
    "anticipation": 0.1
  },
  "semantic_embedding": [0.021, -0.134, "... 384 floats"],
  "key_phrases": ["overwhelmed", "work stress", "deadline pressure"]
}
```

**Request Fields**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | ✅ | Unique user identifier |
| `session_id` | string (UUID) | ✅ | Current session ID (from Journal Part 1) |
| `entry_text` | string | ✅ | Raw journal entry text |
| `emotion_vector` | EmotionVector | ✅ | 8-dimensional BERT emotion output |
| `semantic_embedding` | float[] | ✅ | 384-dim Sentence-BERT embedding |
| `key_phrases` | string[] | ❌ | spaCy-extracted key phrases for content search |

**Success Response** `200`
```json
{
  "status": "success",
  "data": {
    "session_id": "sess_xyz789",
    "therapy_mode": "CBT",
    "response": "It sounds like you're carrying a heavy load right now...",
    "memory_context": [
      {
        "session_id": "sess_abc001",
        "timestamp": "2024-11-15T10:30:00Z",
        "summary": "User expressed similar work-related anxiety two weeks ago.",
        "relevance_score": 0.87,
        "therapy_mode": "CBT"
      }
    ],
    "recommendations": [
      {
        "source": "youtube",
        "title": "5-Minute CBT Exercise for Work Stress",
        "url": "https://youtube.com/watch?v=...",
        "relevance_reason": "Matched high fear and sadness scores with CBT mode"
      }
    ],
    "metadata": {
      "therapy_mode_confidence": 0.91,
      "retrieval_latency_ms": 42,
      "generation_latency_ms": 380,
      "total_latency_ms": 422
    }
  }
}
```

**Response Fields**
| Field | Type | Description |
|-------|------|-------------|
| `data.therapy_mode` | string | Auto-selected: `CBT` · `DBT` · `ACT` |
| `data.response` | string | AI-generated therapy response |
| `data.memory_context` | MemoryRecord[] | Top-K semantically relevant past sessions |
| `data.recommendations` | ContentRecommendation[] | YouTube/article suggestions (max 3) |
| `data.metadata.therapy_mode_confidence` | float | Model confidence in selected therapy mode |
| `data.metadata.total_latency_ms` | integer | Full pipeline wall-clock time |

**Error Responses**
| Status | Description |
|--------|-------------|
| 400 | Invalid request body — missing required fields or malformed embedding |
| 422 | Emotion vector values out of range (must be 0.0–1.0) |
| 429 | GPT-4 rate limit exceeded |
| 500 | Internal generation failure |

> **Frontend notes**:
> - Pass `session_id` from Journal Part 1's response directly — do not generate a new one.
> - `memory_context` may be empty for new users with no prior sessions.
> - Display `therapy_mode` as a subtle badge (e.g. "CBT Mode") — do not let users change it.
> - Use `total_latency_ms` for performance monitoring.

---

### `GET /journal/history/{user_id}`
**Summary**: Returns a paginated list of past journal sessions for a user.

**Path Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | Unique user identifier |

**Query Parameters**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | ❌ | `10` | Max sessions to return (1–50) |
| `offset` | integer | ❌ | `0` | Pagination offset |

**Success Response** `200`
```json
{
  "status": "success",
  "data": {
    "user_id": "usr_abc123",
    "total": 42,
    "limit": 10,
    "offset": 0,
    "sessions": [
      {
        "session_id": "sess_xyz789",
        "timestamp": "2024-12-01T09:15:00Z",
        "summary": "Discussed work stress and deadline anxiety.",
        "dominant_emotion": "sadness",
        "therapy_mode": "CBT"
      }
    ]
  }
}
```

**Response Fields**
| Field | Type | Description |
|-------|------|-------------|
| `data.total` | integer | Total sessions for this user |
| `data.sessions[].dominant_emotion` | string | Highest-scoring emotion from the 8-dim vector |
| `data.sessions[].therapy_mode` | string | Mode used in that session |

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | User not found |
| 500 | Internal server error |

> **Frontend notes**: Use `total`, `limit`, and `offset` to implement pagination. Show `dominant_emotion` as a mood indicator icon in the history list.

---

### `GET /journal/insights/{user_id}`
**Summary**: Returns longitudinal emotional trends and PPO-driven personalization metrics for a user. Powered by LSTM temporal analysis over stored sessions.

**Path Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | Unique user identifier |

**Query Parameters**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | ❌ | `30` | Lookback window in days (7 · 14 · 30 · 90) |

**Success Response** `200`
```json
{
  "status": "success",
  "data": {
    "user_id": "usr_abc123",
    "period_days": 30,
    "session_count": 14,
    "emotion_trends": {
      "joy": { "start": 0.2, "end": 0.45, "delta": 0.25, "trend": "improving" },
      "sadness": { "start": 0.7, "end": 0.4, "delta": -0.30, "trend": "improving" },
      "fear": { "start": 0.5, "end": 0.3, "delta": -0.20, "trend": "improving" }
    },
    "therapy_mode_distribution": {
      "CBT": 0.57,
      "DBT": 0.29,
      "ACT": 0.14
    },
    "ppo_score": 0.73,
    "insight_summary": "Consistent reduction in sadness over the past month. CBT exercises appear most effective for this user."
  }
}
```

**Response Fields**
| Field | Type | Description |
|-------|------|-------------|
| `data.emotion_trends` | object | Per-emotion start/end/delta over the period |
| `data.emotion_trends[emotion].trend` | string | `improving` · `declining` · `stable` |
| `data.therapy_mode_distribution` | object | Fraction of sessions per therapy mode |
| `data.ppo_score` | float (0–1) | PPO reinforcement learning personalization score |
| `data.insight_summary` | string | Human-readable AI-generated summary |

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | User not found or insufficient session data |
| 500 | Internal server error |

> **Frontend notes**:
> - Require at least **3 sessions** before surfacing insights — show an empty state otherwise.
> - Render `emotion_trends` as a line chart (e.g. Recharts / Chart.js).
> - `ppo_score` can be shown as a "Personalization Progress" indicator (0–100%).

---

---

## Frontend Integration Guide

### Typical Request Flow

```
Frontend (Journal UI)               Journal Part 1          Journal Part 2
      |                                   |                        |
      |--- POST /journal/ingest --------->|                        |
      |<-- { session_id, emotion_vector,  |                        |
      |      semantic_embedding, ... } ---|                        |
      |                                   |                        |
      |--- POST /journal/generate ----------------------->|        |
      |        { user_id, session_id,                    |        |
      |          emotion_vector, embedding, ... }         |        |
      |<-- { therapy_mode, response,                      |        |
      |      memory_context, recommendations, ... } ------|        |
      |                                                            |
      |--- GET /journal/insights/{user_id} ----------------------->|
      |<-- { emotion_trends, ppo_score, insight_summary } ---------|
```

### Error Handling
- On `429`: back off **5 seconds** before retrying `/journal/generate`.
- On `500`: show a generic "something went wrong" toast — do not expose raw error details to users.
- On `404` from `/journal/history` or `/journal/insights`: render empty state UI, not an error screen.

---

## Error Reference

### HTTP Error Codes
| Status | Description |
|--------|-------------|
| `400` | Bad request — missing or malformed body |
| `404` | Resource not found (user or session) |
| `422` | Validation error — field value out of allowed range |
| `429` | Rate limited — GPT-4 quota exceeded |
| `500` | Internal server error |

### Common Error Scenarios
| Scenario | Status | Recommended Frontend Action |
|----------|--------|-----------------------------|
| Missing `emotion_vector` in request | 400 | Ensure Journal Part 1 output is passed in full |
| Embedding dimension mismatch | 422 | Verify Sentence-BERT output is 384 floats |
| GPT-4 rate limit | 429 | Back off 5s, show "generating..." with retry |
| Pinecone retrieval failure | 500 | Proceed with response — omit `memory_context` gracefully |
| New user — no history | 200 | `memory_context: []` — handle empty array in UI |

---

## Configuration Reference

| Variable | Default | Frontend Impact |
|----------|---------|-----------------|
| `SHORT_TERM_WINDOW` | `5` | Sessions kept in Redis context |
| `TOP_K_RETRIEVAL` | `3` | Max `memory_context` records returned |
| `MAX_RESPONSE_TOKENS` | `512` | Max length of AI response |
| `RECOMMENDATION_COUNT` | `3` | Max items in `recommendations` array |
| `SERVICE_PORT` | `8001` | Base URL port |
| `MIN_SESSIONS_FOR_INSIGHTS` | `3` | Sessions required before `/insights` returns data |