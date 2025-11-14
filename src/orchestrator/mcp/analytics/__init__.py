"""Analytics and data profiling APIs.

This module provides functions for descriptive analytics,
drift detection, and data quality assessment.
"""

from .describe_data import describe_data
from .detect_drift import detect_drift

__all__ = ["describe_data", "detect_drift"]
