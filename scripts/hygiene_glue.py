#!/usr/bin/env python3
"""Thin wrapper for hygiene report aggregation."""

import sys
from pathlib import Path

# Add src to path for importability
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.steward.glue import main

if __name__ == "__main__":
    main()
