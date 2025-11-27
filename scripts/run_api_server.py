#!/usr/bin/env python3
"""
Run the Orchestrator v2 API server.

Usage:
    python scripts/run_api_server.py
    python scripts/run_api_server.py --port 8080
    python scripts/run_api_server.py --reload

Environment Variables:
    ORCHESTRATOR_API_PORT: Port to run on (default: 8000)
    ORCHESTRATOR_API_HOST: Host to bind to (default: 0.0.0.0)
    ORCHESTRATOR_DEFAULT_LLM_PROVIDER: Default LLM provider (default: anthropic)
    ANTHROPIC_API_KEY: API key for Anthropic (required for BYOK users)
    AWS_DEFAULT_REGION: AWS region for Bedrock (default: us-east-1)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def configure_logging(level: str = "INFO") -> None:
    """Configure logging for the server."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    """Run the API server."""
    parser = argparse.ArgumentParser(
        description="Run the Orchestrator v2 API server",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("ORCHESTRATOR_API_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("ORCHESTRATOR_API_PORT", "8000")),
        help="Port to run on (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Log configuration
    logger.info(f"Starting Orchestrator v2 API server")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Reload: {args.reload}")
    
    # Check for LLM configuration
    if os.environ.get("ANTHROPIC_API_KEY"):
        logger.info("Anthropic API key detected")
    else:
        logger.warning("No ANTHROPIC_API_KEY set - BYOK users will need to provide their own")
    
    if os.environ.get("AWS_DEFAULT_REGION"):
        logger.info(f"AWS region: {os.environ.get('AWS_DEFAULT_REGION')}")
    
    # Import and run uvicorn
    try:
        import uvicorn
    except ImportError:
        logger.error("uvicorn not installed. Run: pip install uvicorn")
        sys.exit(1)
    
    # Run the server
    uvicorn.run(
        "orchestrator_v2.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level.lower(),
    )


if __name__ == "__main__":
    main()
