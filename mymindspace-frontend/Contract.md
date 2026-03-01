# TTS Microservice — API Contract

> **Base URL (HTTP)**: `http://localhost:8000`
> **Base URL (WebSocket)**: `ws://localhost:8000`
> **Version**: 1.0.0
> **Auth**: None (internal microservice — secure with auth proxy in production)
> **Framework**: FastAPI (Python)
> **CORS**: All origins allowed (`*`) — restrict in production

---

## Overview

WebSocket-based Text-to-Speech (TTS) microservice powered by **Groq PlayAI TTS** with real-time chunk streaming. The frontend connects via a persistent WebSocket, sends text, and receives audio chunks progressively as base64-encoded WAV data. HTTP endpoints are available for health monitoring and service discovery.

### Key Characteristics
- Audio format: **WAV at 24 kHz** (base64-encoded in JSON)
- Streaming: **chunk-by-chunk** (text split into ~15-word micro-chunks)
- Max text: **9,000 characters** per request
- Max concurrent WebSocket connections: **10** (configurable)
- Average generation time: **3–6 seconds** (Groq API)

---

## Data Models

### VoiceOption
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Voice identifier to use in requests |
| `model` | string | Underlying TTS model |
| `language` | string | `en` · `ar` |

### AudioChunk
| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | integer | 1-based chunk index |
| `total_chunks` | integer | Total chunks in this request |
| `text_chunk` | string | Text fragment for this chunk |
| `audio_data` | string (base64) | WAV audio bytes, base64-encoded |
| `sample_rate` | integer | Always `24000` Hz |
| `is_final` | boolean | `true` on last chunk |

---

## Reference: Available Voices

### English Voices — `playai-tts` model
`Arista-PlayAI` · `Atlas-PlayAI` · `Basil-PlayAI` · `Briggs-PlayAI` · `Calum-PlayAI` · `Celeste-PlayAI` · `Cheyenne-PlayAI` · `Chip-PlayAI` · `Cillian-PlayAI` · `Deedee-PlayAI` · `Fritz-PlayAI` · `Gail-PlayAI` · `Indigo-PlayAI` · `Mamaw-PlayAI` · `Mason-PlayAI` · `Mikail-PlayAI` · `Mitch-PlayAI` · `Quinn-PlayAI` · `Thunder-PlayAI`

### Arabic Voices — `playai-tts-arabic` model
`Ahmad-PlayAI` · `Amira-PlayAI` · `Khalid-PlayAI` · `Nasser-PlayAI`

### Legacy / Local Voices — `canopylabs/orpheus-v1-english` model
`autumn` *(default)* · `diana` · `hannah` · `austin` · `daniel` · `troy`

> **Default voice**: `Fritz-PlayAI` (Groq) or `autumn` (local fallback)

---

## Standard Response Envelopes

**Success (HTTP)**
```json
{ "status": "healthy", "field": "value" }
```

**Error (HTTP)**
```json
{ "error": "Error description", "detail": "Details" }
```

**WebSocket Error Frame**
```json
{ "type": "error", "message": "Human-readable description", "chunk_id": 1, "total_chunks": 3, "text_chunk": "Text that failed" }
```

---

---

## HTTP Endpoints

---

### `GET /`
**Summary**: Service info and endpoint discovery

**Success Response** `200`
```json
{
  "service": "TTS Microservice",
  "version": "1.0.0",
  "status": "running",
  "model_type": "groq",
  "model": "playai-tts",
  "default_voice": "Fritz-PlayAI",
  "endpoints": {
    "health": "/health",
    "status": "/status",
    "websocket": "/ws/tts",
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
**Summary**: Liveness and readiness check. Use this for frontend startup verification and reconnect guards.

**Success Response** `200`
```json
{
  "status": "healthy",
  "model_status": "loaded",
  "model_type": "groq",
  "groq_configured": true,
  "active_connections": 2,
  "max_connections": 10,
  "configuration": {
    "model": "playai-tts",
    "default_voice": "Fritz-PlayAI",
    "sample_rate": 24000,
    "use_groq": true
  }
}
```

| Response Field | Type | Description |
|----------------|------|-------------|
| `status` | string | `healthy` · `unhealthy` |
| `model_status` | string | `loaded` · `not_loaded` |
| `groq_configured` | boolean | Whether `GROQ_API_KEY` is set |
| `active_connections` | integer | Current WebSocket clients |
| `max_connections` | integer | Configured connection limit |

**Error Responses**
| Status | Description |
|--------|-------------|
| 500 | Service unhealthy — model or config failure |

> **Frontend usage**: Poll this before opening a WebSocket connection. If `groq_configured` is `false` or `model_status` is `not_loaded`, show a service unavailable state.

---

### `GET /status`
**Summary**: Detailed operational status including configuration snapshot.

**Success Response** `200`
```json
{
  "service_info": {
    "name": "TTS Microservice",
    "version": "1.0.0",
    "model_type": "groq",
    "model": "playai-tts",
    "voice": "Fritz-PlayAI"
  },
  "performance": {
    "active_connections": 2,
    "max_connections": 10,
    "model_loaded": true
  },
  "configuration": {
    "use_groq": true,
    "groq_configured": true,
    "sample_rate": 24000,
    "max_text_length": 9000,
    "chunk_size": 200,
    "chunk_size_words": 15,
    "chunk_timeout": 30
  }
}
```

| Response Field | Type | Description |
|----------------|------|-------------|
| `performance.active_connections` | integer | Live WebSocket clients |
| `configuration.max_text_length` | integer | Character limit per TTS request |
| `configuration.chunk_size_words` | integer | Words per streamed audio chunk |

**Error Responses**
| Status | Description |
|--------|-------------|
| 500 | Internal server error |

> **Frontend usage**: Expose this on a developer/debug panel. Use `configuration.max_text_length` to enforce client-side input validation before sending text.

---

### `GET /docs`
**Summary**: Interactive Swagger UI (auto-generated by FastAPI). Not called by frontend directly — useful during development.

---

---

## WebSocket Endpoint

### `WS /ws/tts`
**Summary**: Main TTS streaming endpoint. Establish a single persistent connection per user session. The connection stays alive and can handle multiple sequential TTS requests.

**Connection URL**: `ws://localhost:8000/ws/tts`

**Protocol**: JSON messages in both directions.

> **Connection limit**: Max 10 concurrent clients. If the server is at capacity, the connection will be rejected.

---

## WebSocket Message Protocol

### Client → Server Messages

All client messages follow this envelope:
```json
{ "type": "<message_type>", "data": { } }
```

---

#### `text_input` — Request TTS Generation
Triggers audio generation for the provided text.

```json
{
  "type": "text_input",
  "data": {
    "text": "Text to convert to speech",
    "voice": "Fritz-PlayAI",
    "parameters": {
      "speed": 1.0,
      "pitch": 1.0
    }
  }
}
```

**`data` Fields**
| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `text` | string | ✅ | — | max 9,000 chars | Text to synthesize |
| `voice` | string | ❌ | `Fritz-PlayAI` | Must match a valid voice name | Voice to use |
| `parameters.speed` | number | ❌ | `1.0` | — | Playback speed modifier |
| `parameters.pitch` | number | ❌ | `1.0` | — | Pitch modifier |

> **Frontend notes**:
> - Validate `text.length <= 9000` before sending.
> - If `voice` is omitted, the server uses its configured default.
> - Send only after receiving a `connection` message with `status: "ready"`.

---

#### `ping` — Heartbeat
Keep-alive message. Send periodically to prevent connection timeout.

```json
{
  "type": "ping",
  "data": { "timestamp": 1740729963 }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.timestamp` | integer | Unix timestamp (ms or s) — echoed back in pong |

> **Frontend notes**: Send a ping every **30 seconds** when idle to keep the connection alive.

---

#### `get_status` — Request Connection Status
Request the server's current status over the WebSocket.

```json
{ "type": "get_status" }
```

No `data` field required.

---

#### `cancel_generation` — Cancel In-Progress TTS
Cancel an ongoing generation. The server will stop sending further `audio_chunk` messages for the current request.

```json
{ "type": "cancel_generation" }
```

> **Frontend notes**: Call this when the user navigates away mid-playback or explicitly cancels. No response is guaranteed after cancellation.

---

### Server → Client Messages

---

#### `connection` — Connection Established
Sent immediately after the WebSocket connection is accepted.

```json
{
  "type": "connection",
  "data": {
    "message": "Connected to TTS microservice",
    "status": "ready",
    "supported_voices": ["Fritz-PlayAI", "Celeste-PlayAI", "..."],
    "max_concurrent": 10
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.status` | string | `ready` — safe to send `text_input` |
| `data.supported_voices` | string[] | Full list of valid voice names |
| `data.max_concurrent` | integer | Server-wide connection limit |

> **Frontend notes**: Wait for this message before sending any `text_input`. Populate voice selector dropdowns from `supported_voices`.

---

#### `generation_started` — TTS Processing Began
Sent when the server starts processing a `text_input` request.

```json
{
  "type": "generation_started",
  "data": {
    "total_chunks": 3,
    "text": "Full text being processed"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.total_chunks` | integer | How many `audio_chunk` messages to expect |
| `data.text` | string | The full text being processed (echo) |

> **Frontend notes**: Use `total_chunks` to render a progress bar. Show a loading indicator here.

---

#### `audio_chunk` — Streamed Audio Data
Sent for each text chunk as audio becomes available. Chunks arrive sequentially.

```json
{
  "type": "audio_chunk",
  "data": {
    "chunk_id": 1,
    "total_chunks": 3,
    "text_chunk": "Text for this chunk",
    "audio_data": "<base64-encoded WAV bytes>",
    "sample_rate": 24000,
    "is_final": false
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.chunk_id` | integer | 1-based index of this chunk |
| `data.total_chunks` | integer | Total chunks for this request |
| `data.text_chunk` | string | The text fragment synthesized in this chunk |
| `data.audio_data` | string (base64) | WAV audio bytes — decode before playing |
| `data.sample_rate` | integer | `24000` Hz — always 24 kHz |
| `data.is_final` | boolean | `true` on the last chunk |

> **Frontend notes**:
> - Decode: `const audioBytes = atob(data.audio_data)` then convert to `ArrayBuffer`.
> - Play progressively using the **Web Audio API** or `<audio>` element with Blob URLs.
> - When `is_final === true`, the stream is complete — hide loading state.
> - Suggested pattern: queue chunks into an audio buffer and play them in sequence as they arrive for the lowest perceived latency.

**Decoding Example (JavaScript)**
```js
// Decode base64 WAV chunk
const raw = atob(data.audio_data);
const bytes = new Uint8Array(raw.length).map((_, i) => raw.charCodeAt(i));
const blob = new Blob([bytes], { type: 'audio/wav' });
const url = URL.createObjectURL(blob);
const audio = new Audio(url);
audio.play();
```

---

#### `generation_complete` — All Chunks Sent
Sent after the final `audio_chunk` (with `is_final: true`) has been delivered.

```json
{
  "type": "generation_complete",
  "data": {
    "total_chunks_processed": 3,
    "text": "Full original text",
    "voice_used": "Fritz-PlayAI",
    "generation_time_seconds": 4.2
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.total_chunks_processed` | integer | Number of chunks sent |
| `data.voice_used` | string | Actual voice used (may differ if default was applied) |
| `data.generation_time_seconds` | number | Total wall-clock generation time |

> **Frontend notes**: Log `generation_time_seconds` for performance monitoring. The connection stays open — you can send another `text_input` immediately.

---

#### `pong` — Heartbeat Response
Response to a client `ping`.

```json
{
  "type": "pong",
  "data": {
    "timestamp": 1740729963,
    "server_time": 1740729963.421
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.timestamp` | integer | Client's original timestamp echoed back |
| `data.server_time` | number | Server Unix timestamp at pong time |

> **Frontend notes**: Measure round-trip latency as `Date.now() - (data.timestamp * 1000)`.

---

#### `status` — Status Response
Response to a client `get_status` message.

```json
{
  "type": "status",
  "data": {
    "active_connections": 2,
    "max_connections": 10,
    "model_loaded": true,
    "default_voice": "Fritz-PlayAI"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.active_connections` | integer | Current active WebSocket clients |
| `data.model_loaded` | boolean | Whether TTS model is ready |
| `data.default_voice` | string | Server-configured default voice |

---

#### `error` — Error Notification
Sent when a chunk fails to generate or a message is invalid.

```json
{
  "type": "error",
  "message": "Error description",
  "chunk_id": 1,
  "total_chunks": 3,
  "text_chunk": "Text that caused the error"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Human-readable error description |
| `chunk_id` | integer | Which chunk failed (if applicable) |
| `total_chunks` | integer | Total chunks in the request |
| `text_chunk` | string | Text fragment that failed |

> **Frontend notes**: 
> - A chunk error does **not** necessarily close the connection — the service may continue with the next chunk.
> - Show an in-app toast or banner. Do not close the WebSocket on a chunk error.
> - If the error message contains `"rate limit"` or `429`, back off before retrying.

---

---

## Frontend Integration Guide

### Connection Lifecycle

```
Frontend                           TTS Service
   |                                    |
   |--- HTTP GET /health -------------->|  (pre-check)
   |<-- { status: "healthy", ... } -----|
   |                                    |
   |--- WS CONNECT /ws/tts ------------>|
   |<-- { type: "connection", ... } ----|  (ready to send)
   |                                    |
   |--- { type: "text_input", ... } --->|
   |<-- { type: "generation_started" } -|
   |<-- { type: "audio_chunk" #1 } -----|  (play chunk)
   |<-- { type: "audio_chunk" #2 } -----|  (queue chunk)
   |<-- { type: "audio_chunk" #3, is_final: true } |
   |<-- { type: "generation_complete" }-|
   |                                    |
   |--- { type: "ping" } -------------->|  (every 30s)
   |<-- { type: "pong" } ---------------|
   |                                    |
   |--- WS CLOSE ---------------------->|  (on unmount)
```

### Recommended Frontend State Machine

```
IDLE → CONNECTING → READY → GENERATING → READY
                        ↓
                    CANCELLED
                        ↓
                     READY
```

| State | Description | UI Action |
|-------|-------------|-----------|
| `IDLE` | No connection yet | "Connect" button |
| `CONNECTING` | WS handshake in progress | Spinner |
| `READY` | Connected, `connection` received | Show input, enable send |
| `GENERATING` | Waiting for / receiving chunks | Progress bar, cancel button |
| `ERROR` | WebSocket closed unexpectedly | Reconnect prompt |

### Connection Error Handling
- On WebSocket `onclose` or `onerror`: wait 2 seconds, then retry up to 3 times with exponential backoff.
- Re-verify `/health` before each reconnect attempt.
- Display a banner if `active_connections >= max_connections`.

---

## Error Reference

### HTTP Error Codes
| Status | Description |
|--------|-------------|
| `400` | Bad request — invalid message format |
| `401` | Unauthorized — invalid or missing API key (Groq) |
| `429` | Rate limited — Groq API quota exceeded |
| `500` | Internal server error |

### WebSocket Error Scenarios
| Scenario | `error.message` contains | Recommended Frontend Action |
|----------|--------------------------|-----------------------------|
| Invalid message JSON | `"invalid"` / `"format"` | Log, show dev error |
| Text too long | `"too long"` / `"length"` | Validate client-side (max 9,000 chars) |
| Groq API rate limit | `"rate limit"` | Back off 5s, retry |
| No TTS model available | `"no model"` / `"not available"` | Show service error banner |
| Connection limit reached | `"max connections"` | Show "service busy" message |

---

## Configuration Reference

Key environment variables that affect frontend-visible behavior:

| Variable | Default | Frontend Impact |
|----------|---------|-----------------|
| `TTS_MAX_TEXT_LENGTH` | `9000` | Client-side input char limit |
| `TTS_MAX_CONCURRENT_CONNECTIONS` | `10` | When full, new connections fail |
| `TTS_GROQ_VOICE` | `autumn` | Default voice if not specified |
| `TTS_PORT` | `8000` | Base URL port |

---

## Rate Limiting

Rate limiting is not enforced at the microservice level — it is governed by the **Groq API quota** on the backend. Implement client-side rate limiting to avoid flooding the service:
- Do not send a new `text_input` until `generation_complete` is received.
- Debounce user-triggered TTS requests by at least **500ms**.
