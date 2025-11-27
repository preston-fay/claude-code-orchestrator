"""CORS configuration for the API server."""

import os
from typing import List


def get_cors_origins() -> List[str]:
    """Get list of allowed CORS origins."""
    origins = [
        # Local development
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    
    # Add any additional origins from environment
    extra_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    if extra_origins:
        origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])
    
    return origins


# Regex pattern to match all Railway subdomains
CORS_ORIGIN_REGEX = r"https://.*\.up\.railway\.app"
