# Multi-stage Dockerfile for AI Journal Analysis Pipeline
# Production-ready deployment for Components 2+3+4 + AstraDB Integration

# ===================================
# Stage 1: Base Python Environment
# ===================================
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    gcc \
    g++ \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ===================================
# Stage 2: Dependencies Installation
# ===================================
FROM base as dependencies

# Create app directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt requirements_astra.txt ./

# Install Python dependencies
# Install core requirements first
RUN pip install --no-cache-dir -r requirements.txt

# Install AstraDB specific requirements
RUN pip install --no-cache-dir -r requirements_astra.txt

# Install additional dependencies not in requirements files
RUN pip install --no-cache-dir \
    astrapy>=0.7.0 \
    python-dotenv>=1.0.0 \
    requests>=2.31.0 \
    fastapi>=0.100.0 \
    uvicorn>=0.22.0

# Download spaCy models (required for NLP processing)
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download en_core_web_lg

# ===================================
# Stage 3: Application Setup
# ===================================
FROM dependencies as application

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/models \
    /app/data \
    /app/logs \
    /app/temp \
    /app/backups

# Set correct permissions
RUN chmod +x integration_main.py

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# ===================================
# Stage 4: Production Environment
# ===================================
FROM application as production

# Expose port (for potential API endpoints)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app'); from integration_main import AstraDBIntegrator; integrator = AstraDBIntegrator(); print('Health check passed')" || exit 1

# Set environment variables for production
ENV PYTHONPATH=/app \
    COMPONENT_VERSION=4.0-PRODUCTION \
    PROCESSING_MODE=STRICT-PRODUCTION

# Default command - runs the integration main script
CMD ["python", "integration_main.py"]

# ===================================
# Alternative Commands (commented out)
# ===================================
# For API mode (uncomment if you want to run as a web service):
# CMD ["uvicorn", "api_wrapper:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# For batch processing mode:
# CMD ["python", "-c", "from integration_main import AstraDBIntegrator; integrator = AstraDBIntegrator(); print('Container started successfully')"]

# For interactive mode (development):
# CMD ["/bin/bash"]

# ===================================
# Build Information
# ===================================
LABEL maintainer="MyMindSpace" \
      version="2.2.0" \
      description="AI Journal Analysis Pipeline with AstraDB Integration" \
      components="Emotion Analysis + NER/Temporal + Feature Engineering" \
      databases="AstraDB + Journal CRUD API + Temporal Events"
