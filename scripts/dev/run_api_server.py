#!/usr/bin/env python3
"""
Run the Orchestrator v2 API server.

Usage:
    python scripts/run_api_server.py [--host HOST] [--port PORT]

Example:
    python scripts/run_api_server.py --port 8080
"""

import argparse
import uvicorn


def main():
    """Run the API server."""
    parser = argparse.ArgumentParser(description="Run Orchestrator v2 API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    print(f"\nStarting Orchestrator v2 API server...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    print(f"Health: http://{args.host}:{args.port}/health\n")

    uvicorn.run(
        "orchestrator_v2.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
