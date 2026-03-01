# TTS Microservice

A high-performance WebSocket-based Text-to-Speech microservice powered by Groq's PlayAI TTS with real-time streaming capabilities.

## Features

- **⚡ Ultra-Fast Generation**: Sub-5-second audio generation using Groq PlayAI TTS
- **🔗 Real-time WebSocket Communication**: Bidirectional communication for instant TTS processing
- **📦 Chunk-by-Chunk Streaming**: Texts are processed and streamed as audio chunks become available
- **🎤 Multiple Voice Options**: Support for 19+ English and 4+ Arabic voices
- **🌐 Multiple Concurrent Connections**: Handle multiple clients simultaneously
- **🚀 Production Ready**: Comprehensive error handling, logging, and monitoring
- **🐳 Docker Support**: Easy deployment with containerization

## Architecture

```
TTS Microservice/
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── models/
│   │   ├── groq_tts_model.py   # Groq API integration
│   │   ├── tts_model.py        # Model interface
│   │   └── orpheus_fallback.py # Local fallback (optional)
│   ├── services/
│   │   ├── text_processor.py   # Text preprocessing
│   │   └── audio_generator.py  # Audio generation orchestration
│   ├── websocket/
│   │   └── tts_handler.py      # WebSocket message handlers
│   ├── config/
│   │   └── settings.py         # Configuration management
│   └── utils/
│       └── helpers.py          # Utility functions
├── requirements.txt             # Python dependencies
├── Dockerfile                  # Container configuration
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- Groq API key (get one at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone and navigate to the project directory**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your actual Groq API key
   # GROQ_API_KEY=your_actual_groq_api_key_here
   ```
   
   **Alternative: Set environment variables directly**:
   ```bash
   # Windows
   set GROQ_API_KEY=your_groq_api_key_here
   
   # Linux/macOS
   export GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Start the microservice**:
   ```bash
   python -m app.main
   ```

The service will start on `http://localhost:8000`

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t tts-microservice .
   ```

2. **Run the container**:
   ```bash
   # Option A: Using environment variables
   docker run -p 8000:8000 -e GROQ_API_KEY=your_api_key tts-microservice
   
   # Option B: Using .env file
   docker run -p 8000:8000 --env-file .env tts-microservice
   
   # Option C: Using docker-compose (recommended)
   docker-compose up
   ```

## API Endpoints

### HTTP Endpoints

- **GET /** - Service information and health check
- **GET /health** - Health check endpoint
- **GET /docs** - Interactive API documentation (Swagger UI)

### WebSocket Endpoint

- **WS /ws/tts** - Main TTS streaming endpoint

## Available Voices

### English Voices
- Arista-PlayAI, Atlas-PlayAI, Basil-PlayAI, Briggs-PlayAI
- Calum-PlayAI, Celeste-PlayAI, Cheyenne-PlayAI, Chip-PlayAI
- Cillian-PlayAI, Deedee-PlayAI, **Fritz-PlayAI** (default), Gail-PlayAI
- Indigo-PlayAI, Mamaw-PlayAI, Mason-PlayAI, Mikail-PlayAI
- Mitch-PlayAI, Quinn-PlayAI, Thunder-PlayAI

### Arabic Voices  
- Ahmad-PlayAI, Amira-PlayAI, Khalid-PlayAI, Nasser-PlayAI

## WebSocket Protocol

### Client to Server Messages

#### Text Input for TTS
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

#### Ping
```json
{
  "type": "ping",
  "data": {"timestamp": 1234567890}
}
```

#### Get Status
```json
{
  "type": "get_status"
}
```

#### Cancel Generation
```json
{
  "type": "cancel_generation"
}
```

### Server to Client Messages

#### Connection Established
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

#### Generation Started
```json
{
  "type": "generation_started",
  "data": {
    "total_chunks": 3,
    "text": "Full text being processed"
  }
}
```

#### Audio Chunk
```json
{
  "type": "audio_chunk",
  "data": {
    "chunk_id": 1,
    "total_chunks": 3,
    "text_chunk": "Text for this chunk",
    "audio_data": "base64_encoded_wav_data",
    "sample_rate": 24000,
    "is_final": false
  }
}
```

#### Generation Complete
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

#### Error
```json
{
  "type": "error",
  "message": "Error description",
  "chunk_id": 1,
  "total_chunks": 3,
  "text_chunk": "Text that caused error"
}
```

#### Pong (Response to Ping)
```json
{
  "type": "pong",
  "data": {
    "timestamp": 1234567890,
    "server_time": 1234567890.123
  }
}
```

#### Status Response
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

## Configuration

Environment variables (all optional with sensible defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | `None` | **Required** - Your Groq API key |
| `TTS_HOST` | `0.0.0.0` | Server host address |
| `TTS_PORT` | `8000` | Server port |
| `TTS_DEBUG` | `false` | Enable debug logging |
| `TTS_USE_GROQ` | `true` | Use Groq API (vs local model) |
| `TTS_GROQ_MODEL` | `playai-tts` | Groq TTS model name |
| `TTS_GROQ_VOICE` | `Fritz-PlayAI` | Default voice |
| `TTS_MAX_CONCURRENT_CONNECTIONS` | `10` | Max concurrent WebSocket clients |
| `TTS_MAX_TEXT_LENGTH` | `9000` | Max characters per request |
| `TTS_CHUNK_SIZE` | `200` | Characters per text chunk |
| `TTS_CHUNK_SIZE_WORDS` | `15` | Words per micro-chunk (for Groq API) |
| `TTS_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Performance

### Latency Metrics (Groq API)
- **Average Generation Time**: 3-6 seconds
- **First Audio Chunk**: < 5 seconds
- **Concurrent Users**: 10+ simultaneous connections
- **Throughput**: ~95% faster than local models

### Previous Performance (Local Model)
- **Average Generation Time**: 120+ seconds
- **GPU Requirements**: 8GB+ VRAM
- **Resource Intensive**: High GPU/CPU usage

### Resource Requirements (Current)
- **CPU**: Minimal (API-based)
- **Memory**: < 1GB RAM
- **Network**: Stable internet connection for Groq API
- **Storage**: Minimal (no large model files)

## Integration Examples

### Python Client
```python
import asyncio
import websockets
import json
import base64
import wave

async def tts_client():
    uri = "ws://localhost:8000/ws/tts"
    
    async with websockets.connect(uri) as websocket:
        # Send TTS request
        message = {
            "type": "text_input",
            "data": {
                "text": "Hello from Groq TTS! This is a test of the ultra-fast speech synthesis.",
                "voice": "Fritz-PlayAI"
            }
        }
        await websocket.send(json.dumps(message))
        
        # Receive and save audio chunks
        chunk_count = 0
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "audio_chunk":
                chunk_count += 1
                chunk_data = data["data"]
                audio_bytes = base64.b64decode(chunk_data["audio_data"])
                
                # Save chunk to file
                with open(f"chunk_{chunk_count}.wav", "wb") as f:
                    f.write(audio_bytes)
                
                print(f"Saved chunk {chunk_data['chunk_id']}/{chunk_data['total_chunks']}")
                
                if chunk_data["is_final"]:
                    break
            elif data["type"] == "error":
                print(f"Error: {data['message']}")
                break

# Run the client
asyncio.run(tts_client())
```

### JavaScript/Node.js Client
```javascript
const WebSocket = require('ws');
const fs = require('fs');

const ws = new WebSocket('ws://localhost:8000/ws/tts');

ws.on('open', function() {
    console.log('Connected to TTS service');
    
    // Send TTS request
    const message = {
        type: "text_input",
        data: {
            text: "Hello from JavaScript! Testing Groq TTS integration.",
            voice: "Celeste-PlayAI"
        }
    };
    ws.send(JSON.stringify(message));
});

ws.on('message', function(data) {
    const response = JSON.parse(data);
    
    switch(response.type) {
        case 'audio_chunk':
            const chunkData = response.data;
            const audioBuffer = Buffer.from(chunkData.audio_data, 'base64');
            
            // Save chunk
            fs.writeFileSync(`chunk_${chunkData.chunk_id}.wav`, audioBuffer);
            console.log(`Saved chunk ${chunkData.chunk_id}/${chunkData.total_chunks}`);
            
            if (chunkData.is_final) {
                console.log('All chunks received!');
                ws.close();
            }
            break;
            
        case 'error':
            console.error('TTS Error:', response.message);
            break;
            
        case 'generation_complete':
            console.log('Generation completed:', response.data);
            break;
    }
});
```

### curl Example (HTTP Health Check)
```bash
# Check service health
curl http://localhost:8000/health

# Get service documentation
curl http://localhost:8000/docs
```

## Development

### Running in Development Mode
```bash
# Enable debug logging
export TTS_DEBUG=true
export TTS_LOG_LEVEL=DEBUG

# Start with live reload (if using uvicorn directly)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the standard method
python -m app.main
```

### Code Structure
- **`app/main.py`** - FastAPI application setup and HTTP endpoints
- **`app/websocket/tts_handler.py`** - WebSocket message handling and routing
- **`app/models/groq_tts_model.py`** - Groq API integration and audio generation
- **`app/services/audio_generator.py`** - Text chunking and audio orchestration
- **`app/services/text_processor.py`** - Text preprocessing and validation
- **`app/config/settings.py`** - Configuration management and environment variables

### Adding New Features
1. **New Voices**: Update voice lists in `groq_tts_model.py`
2. **New Message Types**: Add handlers in `tts_handler.py`
3. **New Endpoints**: Add routes in `main.py`
4. **Configuration**: Add settings in `settings.py`

## Deployment

### Docker Deployment (Recommended)
```bash
# Build the image
docker build -t tts-microservice .

# Run with environment variables
docker run -d \
  --name tts-service \
  -p 8000:8000 \
  -e GROQ_API_KEY=your_api_key_here \
  -e TTS_LOG_LEVEL=INFO \
  tts-microservice

# Check logs
docker logs tts-service

# Stop the service
docker stop tts-service
```

### Production Deployment
```bash
# Using docker-compose (create docker-compose.yml)
version: '3.8'
services:
  tts:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - TTS_LOG_LEVEL=INFO
      - TTS_MAX_CONCURRENT_CONNECTIONS=20
    restart: unless-stopped

# Deploy
docker-compose up -d
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tts-microservice
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tts-microservice
  template:
    metadata:
      labels:
        app: tts-microservice
    spec:
      containers:
      - name: tts
        image: tts-microservice:latest
        ports:
        - containerPort: 8000
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: tts-secrets
              key: groq-api-key
---
apiVersion: v1
kind: Service
metadata:
  name: tts-service
spec:
  selector:
    app: tts-microservice
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### Production Considerations
- **Load Balancing**: Use nginx or cloud load balancers for multiple instances
- **API Key Security**: Store Groq API key in secure secret management
- **Rate Limiting**: Implement rate limiting to prevent API quota exhaustion
- **Monitoring**: Set up health checks and monitoring (Prometheus + Grafana)
- **Logging**: Use centralized logging (ELK stack or cloud logging)
- **SSL/TLS**: Enable HTTPS for secure WebSocket connections (WSS)
- **CORS**: Configure appropriate CORS policies for web clients

## Troubleshooting

### Common Issues

1. **"No TTS model available" Error**
   ```bash
   # Check if GROQ_API_KEY is set
   echo $GROQ_API_KEY  # Linux/macOS
   echo %GROQ_API_KEY%  # Windows
   
   # Verify API key is valid
   curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models
   ```

2. **WebSocket Connection Refused**
   - Ensure server is running on correct port
   - Check firewall settings
   - Verify client WebSocket URL format: `ws://localhost:8000/ws/tts`

3. **Groq API Rate Limits**
   - Monitor API usage in Groq console
   - Implement client-side rate limiting
   - Consider upgrading Groq plan for higher limits

4. **Audio Playback Issues**
   - Generated audio is in WAV format at 24kHz
   - Ensure client properly decodes base64 audio data
   - Check audio codec compatibility

5. **High Memory Usage**
   - Reduce `TTS_MAX_CONCURRENT_CONNECTIONS`
   - Lower `TTS_CHUNK_SIZE` for smaller memory footprint
   - Monitor connection cleanup

### Debug Mode
```bash
# Enable detailed logging
export TTS_DEBUG=true
export TTS_LOG_LEVEL=DEBUG
python -m app.main

# Check logs for detailed error information
```

### Health Checks
```bash
# HTTP health check
curl http://localhost:8000/health

# WebSocket connection test
python -c "
import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://localhost:8000/ws/tts') as ws:
            print('✅ WebSocket connection successful')
    except Exception as e:
        print(f'❌ WebSocket connection failed: {e}')

asyncio.run(test())
"
```

## API Reference

### Error Codes
- **400**: Bad Request (invalid message format)
- **401**: Unauthorized (invalid API key)
- **429**: Rate Limited (too many requests)
- **500**: Internal Server Error

### Message Validation
- **Text Length**: Maximum 9,000 characters
- **Voice Names**: Must match available voice list
- **Message Format**: Must be valid JSON with required fields

## Performance Tuning

### Optimization Tips
1. **Text Chunking**: Adjust `TTS_CHUNK_SIZE` based on use case
2. **Connection Limits**: Set appropriate `TTS_MAX_CONCURRENT_CONNECTIONS`
3. **Caching**: Consider implementing audio caching for repeated texts
4. **Load Balancing**: Deploy multiple instances for high traffic

### Monitoring Metrics
- WebSocket connection count
- Audio generation latency
- Groq API response times
- Error rates and types
- Memory and CPU usage

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -r requirements.txt`
4. Make changes and test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings for public functions
- Include unit tests for new features

## License

This project is licensed under the MIT License. See LICENSE file for details.

The Groq API has its own terms of service and usage policies. Please review Groq's documentation for commercial usage guidelines.

## Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Documentation**: Check this README and the `/docs` endpoint
- **API Keys**: Get your Groq API key at [console.groq.com](https://console.groq.com)
- **Community**: Join discussions in the project's GitHub Discussions

---

**Powered by Groq PlayAI TTS** 🚀