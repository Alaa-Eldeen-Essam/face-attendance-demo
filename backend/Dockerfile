# Multi-stage build for CPU variant
# Reduces image size from ~2GB to ~900MB
# Optimized for portability and general deployment

FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install minimal build dependencies for pip
# Skip full build-essential which includes many unnecessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python packages to user directory
# Using --only-binary to prefer wheels (faster, no compilation needed)
RUN pip install --user --no-cache-dir --only-binary :all: -r requirements.txt || \
    pip install --user --no-cache-dir -r requirements.txt

# ========== Runtime Stage ==========
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install only runtime dependencies (minimal image)
# Note: opencv-python provides its own compiled binaries via pip wheels
# These are X11/rendering libraries needed by various Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY backend/ /app/
COPY frontend/ /frontend/

# Create non-root user for security (optional but recommended)
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose API port
EXPOSE 8000

# Run FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
