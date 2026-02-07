# LiveAI Real-Time Market Risk Intelligence Platform
# Production Dockerfile

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATHWAY_PERSISTENT_STORAGE=/app/pathway_state

# Create necessary directories
RUN mkdir -p /app/pathway_state /app/data

# Expose ports
EXPOSE 8501

# Default command (can be overridden)
CMD ["python", "app.py"]
