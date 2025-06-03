# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add gunicorn for production server
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY app.py .
COPY create_indexes.py .

# Create a non-root user to run the app
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run uses PORT environment variable
ENV PORT 8080
EXPOSE 8080

# Use gunicorn with optimal settings for Cloud Run
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --log-level info app:app 