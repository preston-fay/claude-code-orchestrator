FROM python:3.11-slim

# Cache bust: 2025-11-27-v1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies - copy early to bust cache when requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway overrides with $PORT)
EXPOSE 8000

# Start the V2 API server with shell expansion for $PORT
CMD sh -c "python startup_check.py && uvicorn orchestrator_v2.api.server:app --host 0.0.0.0 --port $PORT"
