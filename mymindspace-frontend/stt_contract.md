# Speech-to-Text (STT) Microservice — API Contract

> **Base URL (HTTP)**: `http://localhost:8000`
> **Version**: 1.0.0
> **Auth**: None (internal microservice — secure with auth proxy in production)
> **Framework**: FastAPI (Python)
> **CORS**: All origins allowed (`*`) — restrict in production

---

## Overview

HTTP microservice that accepts audio file uploads and returns transcribed text using **AssemblyAI's real-time streaming transcription API** over WebSocket. The frontend sends audio via multipart form POST and receives the final transcript in a single JSON response.

### Key Characteristics
- Transcription engine: **AssemblyAI Streaming v3** (`wss://streaming.assemblyai.com/v3/ws`)
- Audio input: **Multipart file upload** (WAV, MP3, OGG, WebM)
- Audio processing: Internal conversion to **16 kHz, mono, 16-bit PCM** before transmission
- Chunk size: **1,600 bytes** per WebSocket send (≈100 ms @ 16 kHz)
- Response: **Synchronous** — waits for full transcript before returning
- Average processing time: dependent on audio length + AssemblyAI turnaround

---

## Data Models

### TranscribeResponse
| Field | Type | Description |
|-------|------|-------------|
| `transcript` | string | Full transcribed text from the audio file |

### HealthResponse
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `healthy` when service is running |
| `timestamp` | string (ISO) | Server time at the moment of the check |

---

## Standard Response Envelopes

**Success**
```json
{ "transcript": "Transcribed text here." }
```

**Error**
```json
{ "detail": "Error description" }
```

---

---

## HTTP Endpoints

---

### `GET /`
**Summary**: Service liveness indicator and basic info.

**Success Response** `200`
```json
{
  "message": "Speech-to-Text API is running"
}
```

---

### `GET /health`
**Summary**: Liveness check. Use before sending audio to confirm the service is up.

**Success Response** `200`
```json
{
  "status": "healthy",
  "timestamp": "2025-09-21T10:30:00.123456"
}
```

| Response Field | Type | Description |
|----------------|------|-------------|
| `status` | string | Always `healthy` when the service is reachable |
| `timestamp` | string (ISO) | Current server time |

> **Frontend usage**: Poll before making a transcription request. If the endpoint is unreachable or returns a non-200 status, show a "Service Unavailable" state and block audio submission.

---

### `POST /transcribe`
**Summary**: Upload an audio file and receive its full transcript. Processing is **synchronous** — the response is returned only after the complete transcript is available.

**Content-Type**: `multipart/form-data`

**Form Fields**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | ✅ | Audio file to transcribe |

**Supported MIME Types**
| MIME Type | Format |
|-----------|--------|
| `audio/wav` | WAV |
| `audio/mpeg` | MP3 |
| `audio/mp3` | MP3 |
| `audio/ogg` | OGG |
| `audio/webm` | WebM |

**Success Response** `200`
```json
{
  "transcript": "Hello, this is the transcribed text from your audio file."
}
```

**Error Responses**
| Status | Condition |
|--------|-----------|
| `400` | Unsupported file type |
| `400` | Empty audio file |
| `500` | AssemblyAI connection failed or internal processing error |

> **Frontend notes**:
> - Validate the file's MIME type client-side before uploading to avoid unnecessary round trips.
> - This endpoint blocks until transcription is complete. Show a loading/spinner state while waiting.
> - If `transcript` is an empty string, the audio contained no detectable speech — inform the user and allow retry.

---

### `POST /transcribe-raw`
**Summary**: Upload raw PCM audio bytes and receive the transcript. Intended for direct microphone capture pipelines that already produce 16 kHz mono 16-bit PCM data.

**Content-Type**: `application/octet-stream`

**Form Fields**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | ✅ | Raw PCM audio — **must be 16 kHz, mono, 16-bit** |

**Success Response** `200`
```json
{
  "transcript": "Transcribed text from raw audio data."
}
```

**Error Responses**
| Status | Condition |
|--------|-----------|
| `400` | Wrong content type (must be `application/octet-stream`) |
| `400` | Empty audio data |
| `500` | AssemblyAI connection failed or internal processing error |

> **Frontend notes**:
> - Use this endpoint when capturing audio directly from the browser's `MediaRecorder` API in PCM format.
> - Do **not** use this for standard file uploads — use `POST /transcribe` instead.
> - The service does **not** convert raw audio; ensure the stream matches the required format exactly.

---

---

## Internal Processing Pipeline

When a transcription request is received, the service processes audio in this sequence:

```
Client Upload (multipart or raw)
         │
         ▼
 Format Validation
  └─ Reject unsupported MIME types or empty files
         │
         ▼
 Audio Conversion (WAV files only)
  ├─ Detect: channels, sample rate, bit depth
  ├─ Stereo → Mono  (left channel extraction)
  └─ Passthrough if already 16 kHz / mono / 16-bit
         │
         ▼
 WebSocket Connection to AssemblyAI
  └─ wss://streaming.assemblyai.com/v3/ws
     (sample_rate=16000, format_turns=true)
         │
         ▼
 Audio Chunking & Streaming
  └─ 1,600-byte binary chunks (~100ms per chunk)
         │
         ▼
 AssemblyAI Transcription
  ├─ Begin → session established
  ├─ Turn → formatted transcript parts received
  └─ Termination → final transcript assembled
         │
         ▼
 Response to Client
  └─ { "transcript": "..." }
```

---

## Audio Format Requirements

| Parameter | Required Value | Notes |
|-----------|----------------|-------|
| Sample Rate | 16,000 Hz | Required by AssemblyAI streaming API |
| Channels | Mono (1) | Stereo WAV is auto-converted (left channel) |
| Bit Depth | 16-bit PCM | Required by AssemblyAI streaming API |

> **Conversion behaviour**: The service performs a best-effort conversion for WAV files. For non-WAV formats (MP3, OGG, WebM), the raw bytes are forwarded to AssemblyAI as-is. For highest reliability, pre-convert audio to 16 kHz mono WAV before uploading.

---

## Frontend Integration Guide

### Transcription Flow

```
Frontend                              STT Service
   |                                      |
   |--- GET /health ---------------------->|  (pre-check)
   |<-- { status: "healthy" } ------------|
   |                                      |
   |--- POST /transcribe (multipart) ----->|
   |    file: audio.wav                   |
   |                                      |  (service connects to AssemblyAI,
   |                                      |   streams audio, waits for result)
   |<-- { transcript: "..." } ------------|
   |                                      |
   |  (display transcript to user)        |
```

### File Upload Example (JavaScript)

```javascript
const fileInput = document.getElementById('audioFile');
const file = fileInput.files[0];

// Pre-validate MIME type
const allowed = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/ogg', 'audio/webm'];
if (!allowed.includes(file.type)) {
  alert('Unsupported audio format.');
  return;
}

// Build form data
const formData = new FormData();
formData.append('file', file);

// Send request
const response = await fetch('http://localhost:8000/transcribe', {
  method: 'POST',
  body: formData,
});

if (!response.ok) {
  const err = await response.json();
  console.error('Transcription failed:', err.detail);
  return;
}

const data = await response.json();
console.log('Transcript:', data.transcript);
```

### Recommended Frontend State Machine

```
IDLE → UPLOADING → PROCESSING → DONE
                       ↓
                    ERROR
                       ↓
                    IDLE (retry)
```

| State | Description | UI Action |
|-------|-------------|-----------|
| `IDLE` | No active request | Show file picker / record button |
| `UPLOADING` | File POST in flight | Show upload progress indicator |
| `PROCESSING` | Waiting for AssemblyAI transcript | Show spinner / "Transcribing…" label |
| `DONE` | Transcript received | Display transcript text |
| `ERROR` | Non-200 response | Show error message, enable retry |

---

## Error Reference

### HTTP Error Codes
| Status | Description |
|--------|-------------|
| `400` | Bad request — unsupported file type or empty file |
| `500` | Internal error — AssemblyAI WebSocket failure, connection timeout, or processing exception |

### Error Scenarios & Recommended Actions
| Scenario | HTTP Status | Recommended Frontend Action |
|----------|-------------|------------------------------|
| Unsupported audio format uploaded | `400` | Show format hint; list accepted types |
| Empty file submitted | `400` | Validate file size > 0 before sending |
| AssemblyAI connection timeout | `500` | Show retry prompt; check service health |
| AssemblyAI API key invalid / missing | `500` | Show "Service configuration error"; notify admin |
| Audio contains no speech | `200` (empty transcript) | Show "No speech detected" message; allow retry |
| Network error (fetch failure) | — | Show generic connection error; retry after delay |

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PLAY_API_KEY` | *(required)* | AssemblyAI API key (loaded from `.env`) |
| `PORT` | `8000` | Service port (set via `uvicorn` startup) |

> **Note**: The API key is read from the `PLAY_API_KEY` environment variable via `python-dotenv`. The service will start without it but all transcription requests will fail with a `500` error from AssemblyAI. Ensure the key is set before deployment.

---

## AssemblyAI WebSocket Reference

The service internally connects to AssemblyAI's streaming endpoint. This is not exposed to the frontend, but is documented here for debugging purposes.

| Parameter | Value |
|-----------|-------|
| Endpoint | `wss://streaming.assemblyai.com/v3/ws` |
| Auth header | `Authorization: <PLAY_API_KEY>` |
| Query params | `sample_rate=16000&format_turns=true` |
| Binary chunk size | 1,600 bytes |
| Termination signal | `{ "type": "Terminate" }` (JSON text frame) |
| Max connection wait | 10 seconds |
| Max processing wait | 30 seconds |

### AssemblyAI Message Types (Internal)
| Type | Direction | Description |
|------|-----------|-------------|
| `Begin` | Server → Service | Session established; contains `session_id` |
| `Turn` | Server → Service | Partial or formatted transcript segment |
| `Termination` | Server → Service | Session ended; final transcript assembled |