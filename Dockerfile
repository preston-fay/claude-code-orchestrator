# =============================
#    BUILDER STAGE
# =============================
FROM python:3.11-slim as builder

WORKDIR /app

# Install system deps (if needed)
RUN apt-get update && apt-get install -y build-essential git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock* ./
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# =============================
#    RUNTIME STAGE
# =============================
FROM python:3.11-slim as runtime

WORKDIR /app

# Install deps
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy orchestrator code
COPY orchestrator_v2 orchestrator_v2
COPY scripts scripts
COPY .orchestrator .orchestrator 2>/dev/null || true

# Expose port
EXPOSE 8000

# Default command: run FastAPI via uvicorn
CMD ["uvicorn", "orchestrator_v2.main:app", "--host", "0.0.0.0", "--port", "8000"]
