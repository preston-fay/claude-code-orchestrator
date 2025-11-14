"""Visualization and reporting APIs.

This module provides functions for creating plots
and generating HTML reports.
"""

from .plot_distribution import plot_distribution
from .generate_report import generate_report

__all__ = ["plot_distribution", "generate_report"]
