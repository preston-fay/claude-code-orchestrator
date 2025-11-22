"""
Production entrypoint for the Orchestrator API.

This module provides a stable ASGI entrypoint for deployment with
uvicorn or gunicorn in production environments.

Usage:
    # Production (uvicorn)
    uvicorn orchestrator_v2.main:app --host 0.0.0.0 --port 8000

    # Production (gunicorn with uvicorn workers)
    gunicorn orchestrator_v2.main:app -w 4 -k uvicorn.workers.UvicornWorker

    # Development
    python orchestrator_v2/main.py
"""

from orchestrator_v2.api.server import app as api_app

# The FastAPI app exposed for uvicorn / gunicorn
app = api_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "orchestrator_v2.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
