# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_mvp.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_mvp.txt

# Copy application code AND Firebase config
COPY . .
COPY firebase_config.json /app/firebase_config.json

# Create necessary directories
RUN mkdir -p temp logs preprocess_output encoder_output

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "main.py"]