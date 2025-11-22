"""
Feature Orchestration Engine for RSC.

Provides a universal system for submitting, planning, building, and deploying
features across all project types.
"""

from .models import (
    FeatureRequest,
    FeaturePlan,
    FeatureBuildPlan,
    FeatureBuildResult,
    FeatureDetail,
    FeatureStatus,
    BuildStatus,
    RepoChange,
    TestResult,
)
from .repository import FileSystemFeatureRepository
from .service import FeatureOrchestrationService, FeatureOrchestrationError

__all__ = [
    "FeatureRequest",
    "FeaturePlan",
    "FeatureBuildPlan",
    "FeatureBuildResult",
    "FeatureDetail",
    "FeatureStatus",
    "BuildStatus",
    "RepoChange",
    "TestResult",
    "FileSystemFeatureRepository",
    "FeatureOrchestrationService",
    "FeatureOrchestrationError",
]
