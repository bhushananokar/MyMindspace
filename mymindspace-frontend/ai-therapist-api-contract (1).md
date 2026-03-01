# AI Therapist API — API Contract

> **Base URL (HTTP)**: `http://localhost:8000`
> **Base URL (WebSocket)**: `ws://localhost:8000`
> **Version**: 2.0.0
> **Auth**: None (internal microservice — secure with auth proxy in production)
> **Framework**: FastAPI (Python)
> **CORS**: All origins allowed (`*`) — restrict in production

---

## Overview

A comprehensive AI-powered therapy system that conducts fully structured therapy sessions via HTTP REST endpoints and a real-time WebSocket. Powered by **Google Gemini**, the system drives an AI therapist persona (Dr. Maya) through dynamic session phases, automated assessments, treatment planning, homework assignment, and crisis detection. Recommendations and diagnosis documentation are also supported.

### Key Characteristics
- AI Engine: **Google Gemini 2.0 Flash**
- Database: **SQLite** (persistent, local)
- Session phases: `intake → assessment → therapy → goal_setting → homework_assignment → closing → completed`
- Assessments: **PHQ-9** (depression), **GAD-7** (anxiety) — auto-administered and scored
- Crisis detection: real-time monitoring for self-harm/suicidal indicators
- WebSocket: real-time chat for ongoing sessions

---

## Data Models

### Patient
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Auto-generated primary key |
| `name` | string | Patient display name |
| `date_of_birth` | string (ISO) | Optional |
| `created_date` | string (ISO) | Account creation timestamp |
| `detected_symptoms` | string[] | Accumulated symptom list |

### Session
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Session primary key |
| `patient_id` | integer | Foreign key → Patient |
| `session_date` | string (ISO) | Session start timestamp |
| `current_phase` | string | Current `SessionPhase` value |
| `conversation_history` | object[] | Array of `{user, ai, timestamp, phase}` |
| `detected_symptoms` | string[] | Symptoms found in this session |
| `assessment_results` | object | PHQ-9 / GAD-7 scores |
| `generated_goals` | object | Treatment plan output |
| `session_completed` | boolean | `true` when phase reaches `completed` |
| `crisis_flags` | string[] | Crisis indicator tags |
| `total_exchanges` | integer | Number of conversation turns |

### SessionPhase (enum)
`intake` · `assessment` · `therapy` · `goal_setting` · `homework_assignment` · `closing` · `completed`

### TreatmentGoal
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Goal primary key |
| `patient_id` | integer | Foreign key → Patient |
| `session_id` | integer | Session that generated this goal |
| `description` | string | SMART goal text |
| `status` | string | `active` · `completed` |
| `current_progress` | integer | 0–100 |

### HomeworkAssignment
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Assignment primary key |
| `patient_id` | integer | Foreign key → Patient |
| `session_id` | integer | Originating session |
| `type` | string | Assignment type (e.g., `thought_record`) |
| `description` | string | Full assignment instructions |
| `completed` | boolean | Completion status |
| `due_date` | string (ISO) | Deadline (default: 7 days from creation) |

### DiagnosisDocument
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Diagnosis primary key |
| `patient_id` | integer | Foreign key → Patient |
| `session_id` | integer | Originating session |
| `diagnosis_name` | string | Clinical diagnosis label |
| `icd_code` | string | ICD-10 code |
| `severity` | string | `mild` · `moderate` · `severe` |
| `notes` | string | Clinical notes |
| `created_at` | string (ISO) | Creation timestamp |

---

## Standard Response Envelopes

**Success (HTTP)**
```json
{ "field": "value" }
```

**Error (HTTP)**
```json
{ "detail": "Error description" }
```

**WebSocket Message (Server → Client)**
```json
{
  "response": "AI therapist message",
  "phase": "assessment",
  "phase_changed": true,
  "conversation_count": 4,
  "detected_symptoms": ["anxiety"],
  "session_completed": false,
  "crisis_detected": false
}
```

---

---

## HTTP Endpoints

---

### `GET /health`
**Summary**: Service liveness check.

**Success Response** `200`
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00",
  "version": "2.0.0",
  "features": [
    "Interactive AI Therapy Sessions",
    "Automated Assessment Conducting",
    "Dynamic Phase Transitions",
    "AI-Generated Treatment Plans",
    "Crisis Detection",
    "Session Transcripts",
    "Real-time WebSocket Chat",
    "Content & Lifestyle Recommendations",
    "Diagnosis Documentation"
  ]
}
```

> **Frontend usage**: Poll before connecting. If status is not `healthy`, show service unavailable state.

---

### `GET /analytics`
**Summary**: System-wide usage and clinical statistics.

**Success Response** `200`
```json
{
  "total_patients": 120,
  "total_sessions": 340,
  "completed_sessions": 210,
  "total_diagnoses": 95,
  "completion_rate": 61.76,
  "average_session_exchanges": 14.3,
  "common_symptoms": { "anxiety": 89, "depression": 67 },
  "diagnosis_distribution": { "GAD": 45, "MDD": 30 },
  "system_uptime": "2025-01-15T10:30:00"
}
```

---

### `GET /admin/fix-database`
**Summary**: Patches missing database schema columns. Use once on first deploy or after schema changes.

**Success Response** `200`
```json
{ "message": "Database schema fixed" }
```

---

---

## Patient Endpoints

---

### `POST /patients`
**Summary**: Register a new patient.

**Request Body**
```json
{
  "name": "Jane Doe",
  "date_of_birth": "1990-05-12"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Patient full name |
| `date_of_birth` | string | ❌ | ISO date format |

**Success Response** `201`
```json
{
  "id": 1,
  "name": "Jane Doe",
  "created_date": "2025-01-15T10:30:00"
}
```

---

### `GET /patients/{patient_id}/sessions`
**Summary**: Get all sessions for a patient, ordered most-recent first.

**Path Parameters**
| Param | Type | Description |
|-------|------|-------------|
| `patient_id` | integer | Patient ID |

**Success Response** `200` — Array of Session objects.

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | Patient not found |

---

### `GET /patients/{patient_id}/dashboard`
**Summary**: Comprehensive patient overview — recent sessions, active goals, pending homework.

**Success Response** `200`
```json
{
  "patient": { "id": 1, "name": "Jane Doe" },
  "recent_sessions": [],
  "active_goals": [],
  "pending_homework": [],
  "latest_session": {},
  "summary": {
    "total_sessions": 3,
    "active_goals": 2,
    "pending_homework": 1,
    "last_session": "2025-01-14T09:00:00",
    "detected_symptoms": ["anxiety", "insomnia"]
  }
}
```

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | Patient not found |

---

---

## Session Endpoints

---

### `POST /sessions/start`
**Summary**: Start a new therapy session for a patient. Returns the AI therapist's opening greeting.

**Request Body**
```json
{
  "patient_id": 1
}
```

**Success Response** `200`
```json
{
  "session_id": 42,
  "patient_name": "Jane Doe",
  "initial_message": "Hello Jane, I'm Dr. Maya. How are you feeling today?",
  "phase": "intake"
}
```

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | Patient not found |

> **Frontend notes**: Store `session_id` — it is required for all subsequent session calls. Display `initial_message` immediately as the first AI turn.

---

### `POST /sessions/chat`
**Summary**: Send a patient message and receive the AI therapist's response. Handles phase transitions, assessment triggers, and crisis detection automatically.

**Request Body**
```json
{
  "session_id": 42,
  "message": "I've been feeling really anxious about work lately."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | integer | ✅ | Active session ID |
| `message` | string | ✅ | Patient's message text |

**Success Response** `200`
```json
{
  "response": "I understand. Can you tell me more about what's been causing that anxiety?",
  "phase": "intake",
  "phase_changed": false,
  "conversation_count": 2,
  "detected_symptoms": ["anxiety"],
  "session_completed": false,
  "crisis_alert": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | AI therapist's reply |
| `phase` | string | Current session phase |
| `phase_changed` | boolean | Whether phase transitioned this turn |
| `conversation_count` | integer | Total turns so far |
| `detected_symptoms` | string[] | Cumulative detected symptoms |
| `session_completed` | boolean | `true` when session is done |
| `crisis_alert` | string \| null | Crisis message if detected, else `null` |

**Error Responses**
| Status | Description |
|--------|-------------|
| 400 | Session already completed |
| 404 | Session not found |

> **Frontend notes**: If `crisis_alert` is non-null, render a prominent safety banner. If `session_completed` is `true`, stop accepting input and redirect to session summary.

---

### `GET /sessions/{session_id}`
**Summary**: Get full session details including conversation history, goals, homework, and assessment results.

**Success Response** `200` — Full Session object including nested `goals` and `homework` arrays.

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | Session not found |

---

### `GET /sessions/{session_id}/export`
**Summary**: Export session as a structured transcript object with full conversation, insights, and treatment plan.

**Success Response** `200` — Full session transcript object.

---

---

## Goals & Homework Endpoints

---

### `POST /homework/{homework_id}/complete`
**Summary**: Mark a homework assignment as completed.

**Request Body**
```json
{
  "notes": "Completed 5 thought records this week. Very helpful!",
  "rating": 4
}
```

**Success Response** `200`
```json
{ "message": "Homework marked as completed", "homework_id": 7 }
```

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | Homework not found |

---

### `GET /goals/{goal_id}/progress`
**Summary**: Update the progress percentage on a treatment goal.

**Query Parameters**
| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `progress` | integer | ✅ | 0–100 | New progress value |

**Success Response** `200`
```json
{ "message": "Goal progress updated", "goal_id": 3, "progress": 75 }
```

**Error Responses**
| Status | Description |
|--------|-------------|
| 400 | Progress out of range |
| 404 | Goal not found |

---

---

## Recommendation Endpoints

---

### `POST /sessions/{session_id}/recommendations`
**Summary**: Generate content and lifestyle recommendations based on the completed session conversation.

**Request Body**
```json
{
  "count": 5
}
```

**Success Response** `200`
```json
{
  "content_recommendations": [],
  "lifestyle_recommendations": [],
  "session_analysis": {},
  "recommendation_metadata": {}
}
```

**Error Responses**
| Status | Description |
|--------|-------------|
| 400 | Session has no conversation history |
| 404 | Session not found |

---

### `POST /sessions/{session_id}/content-recommendations`
**Summary**: Generate content-only recommendations (YouTube, articles, podcasts).

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `count` | integer | `5` | Number of recommendations |

**Success Response** `200` — Array of content recommendation objects.

---

### `GET /sessions/{session_id}/recommendations/export`
**Summary**: Export all recommendations for a session in a structured format.

**Success Response** `200`
```json
{
  "patient_info": {},
  "session_analysis": {},
  "content_recommendations": { "total_count": 5, "recommendations": [] },
  "lifestyle_recommendations": { "total_count": 3, "recommendations": [] },
  "export_info": { "exported_at": "2025-01-15T10:30:00", "format_version": "1.0" }
}
```

---

### `GET /analytics/recommendations`
**Summary**: Aggregate recommendation analytics across all sessions.

**Success Response** `200`
```json
{
  "total_recommendations": 230,
  "content_type_distribution": {},
  "activity_type_distribution": {},
  "insights": {
    "most_recommended_content": "mindfulness_video",
    "most_recommended_activity": "journaling",
    "top_therapeutic_theme": "anxiety_management",
    "most_common_symptom": "anxiety"
  },
  "generated_at": "2025-01-15T10:30:00"
}
```

---

---

## Diagnosis Documentation Endpoints

---

### `POST /diagnosis`
**Summary**: Create a diagnosis document for a patient session.

**Request Body**
```json
{
  "patient_id": 1,
  "session_id": 42,
  "diagnosis_name": "Generalized Anxiety Disorder",
  "icd_code": "F41.1",
  "severity": "moderate",
  "notes": "Patient presents with persistent worry and somatic symptoms."
}
```

**Success Response** `201` — Full DiagnosisDocument object.

---

### `GET /diagnosis/{diagnosis_id}`
**Summary**: Retrieve a specific diagnosis document.

**Success Response** `200` — DiagnosisDocument object.

**Error Responses**
| Status | Description |
|--------|-------------|
| 404 | Diagnosis not found |

---

### `PUT /diagnosis/{diagnosis_id}`
**Summary**: Update an existing diagnosis document.

**Request Body** — Any subset of DiagnosisDocument fields.

**Success Response** `200` — Updated DiagnosisDocument object.

---

### `POST /test/recommendations`
**Summary**: Developer test endpoint — runs recommendation engine against a hardcoded sample conversation.

**Success Response** `200` — Full recommendation result object.

---

---

## WebSocket Endpoint

### `WS /ws/{session_id}`
**Summary**: Real-time therapy chat for an existing session. Maintains a persistent connection per session. Equivalent to `POST /sessions/chat` but event-driven.

**Connection URL**: `ws://localhost:8000/ws/{session_id}`

**Path Parameters**
| Param | Type | Description |
|-------|------|-------------|
| `session_id` | integer | Must be an existing, non-completed session ID |

---

## WebSocket Message Protocol

### Client → Server

```json
{ "message": "I've been struggling to sleep lately." }
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✅ | Patient's message text |

---

### Server → Client

```json
{
  "response": "Sleep issues are common with anxiety. Let's explore that further.",
  "phase": "therapy",
  "phase_changed": true,
  "conversation_count": 6,
  "detected_symptoms": ["anxiety", "insomnia"],
  "session_completed": false,
  "crisis_detected": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | AI therapist's reply |
| `phase` | string | Current session phase |
| `phase_changed` | boolean | Phase transitioned this turn |
| `conversation_count` | integer | Total turns in session |
| `detected_symptoms` | string[] | Cumulative detected symptoms |
| `session_completed` | boolean | Session has reached `completed` phase |
| `crisis_detected` | boolean | Crisis indicators found |

**WebSocket Error Frame**
```json
{ "error": "Session not found or completed" }
```

> **Frontend notes**: If `crisis_detected` is `true`, show safety resources immediately. If `session_completed` is `true`, close the WebSocket and navigate to session summary.

---

---

## Frontend Integration Guide

### Session Lifecycle

```
Frontend                              AI Therapist Service
   |                                         |
   |--- HTTP GET /health ------------------>|  (pre-check)
   |<-- { status: "healthy" } -------------|
   |                                         |
   |--- POST /patients ---------------------->|  (register or skip if existing)
   |<-- { id: 1 } --------------------------|
   |                                         |
   |--- POST /sessions/start -------------->|
   |<-- { session_id, initial_message } ----|
   |                                         |
   |--- WS CONNECT /ws/{session_id} ------->|
   |--- { message: "I feel anxious" } ----->|
   |<-- { response, phase, symptoms } ------|
   |--- { message: "..." } ---------------->|
   |<-- { session_completed: true } --------|
   |                                         |
   |--- GET /sessions/{id} ---------------->|  (fetch summary)
   |--- POST /sessions/{id}/recommendations>|  (optional)
```

### Recommended Frontend State Machine

```
IDLE → STARTING → IN_SESSION → COMPLETED
                     ↓
                  CRISIS
                     ↓
                SAFETY_PROMPT
```

| State | Description | UI Action |
|-------|-------------|-----------|
| `IDLE` | No active session | "Start Session" button |
| `STARTING` | `POST /sessions/start` in flight | Spinner |
| `IN_SESSION` | WebSocket active, receiving responses | Chat UI, phase indicator |
| `CRISIS` | `crisis_detected: true` received | Safety banner, emergency resources |
| `COMPLETED` | `session_completed: true` | Summary view, recommendation CTA |

### Phase Progress Display

Show a progress bar using the ordered phase list:

```
intake → assessment → therapy → goal_setting → homework_assignment → closing → completed
```

Advance the indicator each time `phase_changed: true` is received.

---

## Error Reference

### HTTP Error Codes
| Status | Description |
|--------|-------------|
| `400` | Bad request — e.g., session already completed, progress out of range |
| `404` | Resource not found — patient, session, goal, or homework |
| `500` | Internal server error — AI API failure or database error |

### WebSocket Error Scenarios
| Scenario | `error` value | Recommended Frontend Action |
|----------|---------------|-----------------------------|
| Session not found | `"Session not found or completed"` | Redirect to session list |
| AI API failure | `"Error: ..."` | Show retry prompt |
| Invalid JSON sent | Generic error | Log, show dev warning |

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(required)* | Google Gemini API key |
| `DATABASE_PATH` | `therapy.db` | SQLite file path |
| `PORT` | `8000` | Service port |
