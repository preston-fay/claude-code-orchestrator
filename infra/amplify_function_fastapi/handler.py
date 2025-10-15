"""AWS Lambda handler for FastAPI using Mangum."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from mangum import Mangum
    from src.server.app import app

    # Create Lambda handler
    handler = Mangum(app, lifespan="off")

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure mangum is installed: pip install mangum")

    def handler(event, context):
        """Fallback handler if imports fail."""
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Server configuration error - mangum not installed"}',
        }
