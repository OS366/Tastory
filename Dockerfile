# Multi-stage build for better caching and smaller final image
FROM python:3.11-slim as base

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir gunicorn

# Dependencies stage (highly cacheable)
FROM base as dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM dependencies as production
WORKDIR /app

# Copy application code (changes most frequently)
COPY app.py nutritional_database.py ./

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Runtime configuration
ENV PORT=8080
EXPOSE 8080

# Optimized startup command
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --log-level info app:app
