# Multi-stage build for efficiency
FROM node:18-alpine AS frontend-builder

WORKDIR /app/rsg-ui

# Copy ONLY package files first (for caching)
COPY rsg-ui/package.json rsg-ui/package-lock.json ./

# Install ALL dependencies (including dev deps for building)
RUN npm ci

# Copy ONLY source files needed for build (not node_modules!)
COPY rsg-ui/src ./src
COPY rsg-ui/public ./public
COPY rsg-ui/index.html ./index.html
COPY rsg-ui/vite.config.ts ./vite.config.ts
COPY rsg-ui/tsconfig*.json ./

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
