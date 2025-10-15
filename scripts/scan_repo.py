#!/usr/bin/env python3
"""Thin wrapper for repository scanner."""

import sys
from pathlib import Path

# Add src to path for importability
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.steward.scanner import main

if __name__ == "__main__":
    main()
