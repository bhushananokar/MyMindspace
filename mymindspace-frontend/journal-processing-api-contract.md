# Journal Processing API — API Contract

> **Base URL (HTTP)**: `http://localhost:8001` *(configurable)*
> **Version**: 1.0.0
> **Auth**: None (internal microservice — secure with auth proxy in production)
> **Framework**: FastAPI (Python)
> **CORS**: All origins allowed (`*`) — restrict in production

---

## Overview

HTTP microservice that ingests a journal entry ID, runs it through the full ML pipeline (Emotion Analysis → Semantic Analysis → Feature Engineering), and stores the resulting embeddings and feature vectors in AstraDB. Acts as the integration layer between the journal CRUD API and the vector database collections.

### Key Characteristics
- Processing pipeline: **Components 2 + 3 + 4** (Emotion → Semantic → Feature Engineering)
- Embedding dimensions: **768D** primary, **384D** lightweight, **90D** feature vector
- Storage targets: `chat_embeddings` and `semantic_search` AstraDB collections
- Execution modes: **immediate** (synchronous) or **background** (async queue)
- Source data: fetched live from the **Journal CRUD API** by journal ID
- Average processing time: **< 500ms** end-to-end

---

## Data Models

### JournalProcessRequest
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `journal_id` | string | ✅ | — | Firestore journal entry ID |
| `user_id` | string | ✅ | — | User identifier |
| `trigger_immediate` | boolean | ❌ | `true` | `true` = synchronous; `false` = background task |

### JournalProcessResponse
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether processing succeeded |
| `message` | string | Human-readable result description |
| `processing_time_ms` | number | End-to-end pipeline duration in milliseconds |
| `entry_id` | string | The processed journal entry ID |

### UserHistoryContextRequest
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | ✅ | User identifier |

### UserHistoryContextResponse
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether retrieval succeeded |
| `message` | string | Human-readable result description |
| `user_history_context` | object \| null | User's aggregated history context |

### UserHistoryContext (object shape)
| Field | Type | Description |
|-------|------|-------------|
| `writing_frequency_baseline` | number | Average entries per week |
| `emotional_baseline` | object | Map of emotion → baseline score |
| `topic_preferences` | string[] | Most common journal topics |
| `behavioral_patterns` | object | Identified behavioral pattern map |
| `last_entry_timestamp` | string (ISO) | Most recent entry date |
| `total_entries` | integer | Lifetime journal entry count |
| `avg_session_duration` | number | Average writing session length |
| `preferred_writing_times` | string[] | Time-of-day patterns |
| `emotional_volatility` | number | 0.0–1.0 stability score |
| `topic_consistency` | number | 0.0–1.0 topic focus score |
| `social_connectivity` | number | 0.0–1.0 social reference frequency |

---

## Standard Response Envelopes

**Success**
```json
{ "success": true, "message": "...", "entry_id": "abc123" }
```

**Error**
```json
{ "detail": "Error description" }
```

---

---

## HTTP Endpoints

---

### `POST /process-journal`
**Summary**: Process a journal entry through the full ML pipeline and store embeddings in AstraDB.

**Request Body**
```json
{
  "journal_id": "firestore-doc-id-abc123",
  "user_id": "user-uuid-xyz",
  "trigger_immediate": true
}
```

**Behavior by `trigger_immediate`**

| Value | Behavior | Response timing |
|-------|----------|-----------------|
| `true` | Runs pipeline synchronously; returns result with `processing_time_ms` | Waits for completion |
| `false` | Queues as a background task; returns immediately | Returns instantly |

**Success Response** `200`

*Immediate mode:*
```json
{
  "success": true,
  "message": "Journal processed and embeddings stored successfully",
  "processing_time_ms": 342.7,
  "entry_id": "firestore-doc-id-abc123"
}
```

*Background mode:*
```json
{
  "success": true,
  "message": "Journal processing queued successfully",
  "processing_time_ms": null,
  "entry_id": "firestore-doc-id-abc123"
}
```

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | Journal entry not found in source CRUD API, or pipeline returned no result |
| 500 | Pipeline failure — component error or AstraDB write failure |

> **Frontend notes**: Use `trigger_immediate: true` when you need to confirm processing before proceeding (e.g., showing updated embeddings). Use `trigger_immediate: false` for fire-and-forget after a journal save. Check `processing_time_ms` for performance monitoring.

---

### `GET /get-user-history`
**Summary**: Retrieve the aggregated user history context for a given user.

**Query Parameters**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | ✅ | User identifier |

**Success Response** `200`
```json
{
  "success": true,
  "message": "User history context retrieved successfully",
  "user_history_context": {
    "writing_frequency_baseline": 4.5,
    "emotional_baseline": { "joy": 0.6, "sadness": 0.2 },
    "topic_preferences": ["work", "family", "health"],
    "behavioral_patterns": { "morning_writer": true },
    "last_entry_timestamp": "2025-01-14T08:30:00Z",
    "total_entries": 127,
    "avg_session_duration": 12.4,
    "preferred_writing_times": ["morning", "evening"],
    "emotional_volatility": 0.34,
    "topic_consistency": 0.71,
    "social_connectivity": 0.55
  }
}
```

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | No history context found for user |
| 500 | Upstream fetch failure |

> **Frontend notes**: Use this to personalise the journal dashboard — display writing streaks, emotional trends, and topic summaries. If `user_history_context` is `null`, the user has no processed history yet; show an empty-state prompt.

---

---

## What Happens During Processing

When `POST /process-journal` is called, the pipeline runs in this order:

```
Journal CRUD API
       │
       ▼  (fetch by journal_id)
 Component 2: Emotion Analysis
  └─ 8-dimensional emotion vector (fine-tuned BERT)
       │
       ▼
 Component 3: Semantic Analysis
  ├─ 768D primary embedding (Sentence-BERT)
  ├─ 384D lightweight embedding
  ├─ NER: people, locations, organisations
  └─ Temporal event extraction
       │
       ▼
 Component 4: Feature Engineering
  ├─ 90D composite feature vector
  ├─ 25D temporal features
  ├─ 20D emotional features
  ├─ 30D semantic features
  └─ 15D user-context features
       │
       ▼
   AstraDB Write
  ├─ chat_embeddings collection
  └─ semantic_search collection
```

---

## AstraDB Collection Schemas

### `chat_embeddings` — per-entry schema
| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Auto-generated entry ID |
| `user_id` | string (UUID) | Normalised user UUID |
| `entry_id` | string (UUID) | Normalised journal entry UUID |
| `message_content` | string | Raw journal text |
| `message_type` | string | `user_message` · `ai_response` · `system_message` |
| `timestamp` | string (ISO + Z) | Entry creation time |
| `session_id` | string | Session grouping identifier |
| `conversation_context` | string | Auto-generated context description |
| `primary_embedding` | float[] (768D) | High-quality semantic embedding |
| `lightweight_embedding` | float[] (384D) | Fast semantic embedding |
| `text_length` | integer | Character count |
| `processing_time_ms` | number | Pipeline duration |
| `model_version` | string | Component version string |
| `semantic_tags` | string[] | Auto-extracted topic tags |
| `emotion_context` | object | Emotion vector breakdown |
| `entities_mentioned` | object | NER output |
| `temporal_context` | object | Extracted events and dates |
| `feature_vector` | float[] (90D) | Composite feature vector |
| `temporal_features` | float[] (25D) | Temporal sub-features |
| `emotional_features` | float[] (20D) | Emotional sub-features |
| `semantic_features` | float[] (30D) | Semantic sub-features |
| `user_features` | float[] (15D) | User-context sub-features |
| `feature_completeness` | number | 0.0–1.0 data completeness score |
| `confidence_score` | number | 0.0–1.0 pipeline confidence |

### `semantic_search` — per-entry schema
A subset of the `chat_embeddings` schema optimised for vector similarity search. Includes `primary_embedding`, `lightweight_embedding`, `semantic_tags`, `user_id`, `entry_id`, and core metadata fields.

---

## Frontend Integration Guide

### Journal Save → Embedding Flow

```
User saves journal entry
         │
         ▼
Journal CRUD API → stores entry, returns journal_id
         │
         ▼
POST /process-journal  { journal_id, user_id, trigger_immediate: false }
         │
         ▼  (background — non-blocking)
Embeddings stored in AstraDB
         │
         ▼
GET /get-user-history  (on dashboard load)
→ display trends, topics, emotional baseline
```

> For real-time confirmation (e.g., "Your entry has been analysed"), use `trigger_immediate: true` and await the response before navigating.

---

## Error Reference

### HTTP Error Codes
| Status | Description |
|--------|-------------|
| `404` | Journal not found in CRUD API, or user has no history |
| `500` | Pipeline component failure, AstraDB write error, or upstream timeout |

### Failure Scenarios
| Scenario | Recommended Frontend Action |
|----------|-----------------------------|
| `404` on process | Verify `journal_id` exists in CRUD API; retry once |
| `500` on process | Show "Processing failed" toast; allow manual retry |
| `404` on history | Show empty-state for user history dashboard |
| Timeout (background) | No action needed — background task will complete independently |

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `CHAT_EMBEDDINGS_COLLECTION_ENDPOINT` | *(required)* | AstraDB chat embeddings endpoint URL |
| `SEMANTIC_SEARCH_COLLECTION_ENDPOINT` | *(required)* | AstraDB semantic search endpoint URL |
| `JOURNAL_CRUD_ENDPOINT` | `https://journal-crud-service-...run.app` | Source journal CRUD API base URL |
| `USER_HISTORY_CONTEXT_ENDPOINT` | `https://user-history-context-service-...run.app` | User history service base URL |
| `PORT` | `8001` | Service port |
