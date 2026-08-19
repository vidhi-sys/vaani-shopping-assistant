# Dockerfile for Vaani Shopping Assistant Deployment on GCP Cloud Run / AWS App Runner / Docker

FROM python:3.10-slim

# Install system dependencies including ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8000

ENV PORT=8000
ENV WHISPER_MODEL_SIZE=base

# Start FastAPI server
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
