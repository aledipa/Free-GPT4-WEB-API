# Multi-stage build for better optimization
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r freegpt && useradd -r -g freegpt freegpt

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=freegpt:freegpt . .

# Create data directory with proper permissions
RUN mkdir -p /app/src/data && \
    chown -R freegpt:freegpt /app

# Switch to non-root user
USER freegpt

# Set working directory to src
WORKDIR /app/src

# Environment variables
ENV PORT=5500
ENV PYTHONPATH="/app/src"

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/models || exit 1

# Default command
ENTRYPOINT ["python", "FreeGPT4_Server.py"]
CMD ["--enable-gui", "--enable-fast-api", "--password", "admin123"]