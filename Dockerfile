# Multi-stage build for efficiency
FROM node:18-alpine AS frontend-builder

WORKDIR /app/rsg-ui

# Copy package files
COPY rsg-ui/package*.json ./

# Install ALL dependencies (including dev deps for building)
RUN npm ci

# Copy frontend source
COPY rsg-ui/ ./

# Build the React app
RUN npm run build

# Python backend stage
FROM python:3.11-slim

# Cache bust: 2025-11-28-v2
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV RAILWAY_ENVIRONMENT=production
ENV NODE_ENV=production

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from the builder stage
COPY --from=frontend-builder /app/rsg-ui/dist /app/rsg-ui/dist

# Create data directories
RUN mkdir -p /app/data/intake_sessions && \
    chmod 777 /app/data/intake_sessions

# Expose port (Railway overrides with $PORT)
EXPOSE 8000

# Start the V2 API server with frontend serving
CMD sh -c "python startup_check.py && uvicorn orchestrator_v2.api.server:app --host 0.0.0.0 --port $PORT"
