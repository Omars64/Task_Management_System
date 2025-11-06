FROM python:3.11-slim

# Install minimal system dependencies (FreeTDS for pymssql)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    freetds-dev \
    bash \
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory (for local fallback)
RUN mkdir -p /app/uploads

# Create non-root user for better security in production
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose default port (Cloud Run will inject PORT env var)
EXPOSE 8080

# Health check (use PORT env var if set, default to 8080)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD bash -c 'curl -f http://localhost:${PORT:-8080}/api/health || exit 1'

# Use gunicorn for production, binding to the Cloud Run PORT
ENV PORT=8080
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "--workers", "4", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
