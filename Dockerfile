# Multi-stage build for optimized image
FROM python:3.12-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and use a non-root user
RUN useradd --create-home --shell /bin/bash luna

# Set work directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim as production

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash luna

# Copy Python packages from builder
COPY --from=builder /root/.local /home/luna/.local

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=luna:luna . .

# Create voicefiles directory
RUN mkdir -p /app/voicefiles && chown luna:luna /app/voicefiles

# Switch to non-root user
USER luna

# Add local bin to PATH
ENV PATH="/home/luna/.local/bin:$PATH"

# Set Python path
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose port if needed (for health checks)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the application
CMD ["python", "main.py"]