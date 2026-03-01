# Speech-to-Text FastAPI Service

A robust, scalable FastAPI web service that converts speech audio files to text using AssemblyAI's real-time transcription API. This service provides RESTful endpoints for uploading audio files and receiving transcribed text responses.

## 🚀 Features

- **Multiple Audio Formats**: Support for WAV, MP3, OGG, and WebM files
- **Real-time Processing**: Streaming transcription using WebSocket connections
- **RESTful API**: Clean HTTP endpoints with JSON responses
- **Async Processing**: Non-blocking audio processing with FastAPI
- **Health Monitoring**: Built-in health check endpoints
- **CORS Support**: Cross-origin requests enabled for web applications
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Docker Ready**: Containerized deployment with Docker and Docker Compose

## 📋 Prerequisites

- Python 3.8 or higher
- AssemblyAI API key ([Get one here](https://www.assemblyai.com/))
- Audio files for testing (WAV, MP3, OGG, or WebM format)

## 🛠️ Installation

### Option 1: Local Installation

1. **Clone or download the project files**:
   ```bash
   mkdir speech-to-text-api
   cd speech-to-text-api
   # Copy the provided files into this directory
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Update API key**:
   Edit `stt.py` and replace the API key:
   ```python
   API_KEY = "your_assemblyai_api_key_here"
   ```

4. **Run the server**:
   ```bash
   python stt.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn stt:app --host 0.0.0.0 --port 8000 --reload
   ```

### Option 2: Docker Installation

1. **Build the Docker image**:
   ```bash
   docker build -t speech-to-text-api .
   ```

2. **Run the container**:
   ```bash
   docker run -d -p 8000:8000 --name stt-api speech-to-text-api
   ```

3. **Check container status**:
   ```bash
   docker ps
   docker logs stt-api
   ```

4. **Stop the container**:
   ```bash
   docker stop stt-api
   docker rm stt-api
   ```

## 📖 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-21T10:30:00.123456"
}
```

#### 2. Root Endpoint
```http
GET /
```

**Response**:
```json
{
  "message": "Speech-to-Text API is running"
}
```

#### 3. Transcribe Audio File
```http
POST /transcribe
```

**Parameters**:
- `file` (form-data): Audio file to transcribe

**Supported Formats**:
- `audio/wav` - WAV files
- `audio/mpeg` - MP3 files  
- `audio/mp3` - MP3 files
- `audio/ogg` - OGG files
- `audio/webm` - WebM files

**Response**:
```json
{
  "transcript": "Hello, this is the transcribed text from your audio file.",
  "timestamp": "2025-09-21T10:30:00.123456",
  "filename": "my_audio.wav"
}
```

#### 4. Transcribe Raw PCM Audio
```http
POST /transcribe-raw
```

**Parameters**:
- `file` (binary): Raw PCM audio data (16kHz, mono, 16-bit)

**Response**:
```json
{
  "transcript": "Transcribed text from raw audio data.",
  "timestamp": "2025-09-21T10:30:00.123456",
  "audio_length_seconds": 10.5
}
```

### Interactive API Documentation

Once the server is running, access the interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Usage Examples

### Using cURL

1. **Health check**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Transcribe audio file**:
   ```bash
   curl -X POST "http://localhost:8000/transcribe" \
        -H "accept: application/json" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@path/to/your/audio.wav"
   ```

### Using Python Requests

```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')
print(response.json())

# Transcribe audio file
with open('audio_file.wav', 'rb') as f:
    files = {'file': ('audio_file.wav', f, 'audio/wav')}
    response = requests.post('http://localhost:8000/transcribe', files=files)
    result = response.json()
    print(f"Transcript: {result['transcript']}")
```

### Using the Provided Client

Run the included client example:

```bash
python client_example.py path/to/your/audio.wav
```

### Using JavaScript/Frontend

```javascript
// HTML file input element
const fileInput = document.getElementById('audioFile');
const file = fileInput.files[0];

// Create FormData
const formData = new FormData();
formData.append('file', file);

// Send request
fetch('http://localhost:8000/transcribe', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Transcript:', data.transcript);
})
.catch(error => {
    console.error('Error:', error);
});
```

## ⚙️ Configuration

### Environment Variables

You can configure the service using environment variables:

```bash
export ASSEMBLYAI_API_KEY="your_api_key_here"
export API_HOST="0.0.0.0"
export API_PORT="8000"
```

### Audio Processing Settings

The service automatically converts audio to the required format:
- **Sample Rate**: 16kHz
- **Channels**: Mono
- **Bit Depth**: 16-bit PCM

## 🔧 Development

### Project Structure

```
speech-to-text-api/
├── stt.py                     # Main FastAPI application
├── requirements.txt           # Python dependencies
├── client_example.py          # Example client for testing
├── Dockerfile                 # Docker configuration
├── .dockerignore             # Docker ignore file
└── README.md                 # This documentation
```

### Adding New Features

1. **Custom Audio Processing**: Modify the `convert_audio_to_16khz_mono()` function
2. **Additional Endpoints**: Add new routes to the FastAPI app
3. **Authentication**: Implement API key validation middleware
4. **Rate Limiting**: Add rate limiting using `slowapi`

### Running in Development Mode

```bash
uvicorn stt:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag automatically restarts the server when code changes are detected.

## 🚀 Production Deployment

### Performance Optimization

1. **Use Gunicorn with Uvicorn workers**:
   ```bash
   pip install gunicorn
   gunicorn stt:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Set up reverse proxy with Nginx**:
   ```nginx
   server {
       listen 80;
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Docker Production Deployment

1. **Build production image**:
   ```bash
   docker build -t speech-to-text-api:v1.0 .
   ```

2. **Run with resource limits**:
   ```bash
   docker run -d \
     -p 8000:8000 \
     --name stt-api-prod \
     --memory="1g" \
     --cpus="2.0" \
     --restart=unless-stopped \
     speech-to-text-api:v1.0
   ```

3. **Monitor the container**:
   ```bash
   # Check health
   docker exec stt-api-prod curl -f http://localhost:8000/health
   
   # View logs
   docker logs -f stt-api-prod
   
   # Check resource usage
   docker stats stt-api-prod
   ```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: speech-to-text-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: speech-to-text-api
  template:
    metadata:
      labels:
        app: speech-to-text-api
    spec:
      containers:
      - name: stt-api
        image: speech-to-text-api:v1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: speech-to-text-service
spec:
  selector:
    app: speech-to-text-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Security Considerations

1. **API Key Security**: Store API keys in environment variables
2. **Rate Limiting**: Implement rate limiting for