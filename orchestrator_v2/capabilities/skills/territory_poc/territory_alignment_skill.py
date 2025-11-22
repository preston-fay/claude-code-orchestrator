"""
Territory Alignment Skill - Cluster retailers into territories using k-means.

This skill reads scored retailers, adds geographic coordinates, applies k-means
clustering, and produces territory assignments with per-territory KPIs.
"""

import hashlib
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from orchestrator_v2.capabilities.skills.models import BaseSkill, SkillMetadata, SkillResult


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
from orchestrator_v2.capabilities.skills.territory_poc.zip_geo_utils import (
    add_coordinates_to_dataframe,
    calculate_distance_km,
)
from orchestrator_v2.engine.state_models import ArtifactInfo, ProjectState, TokenUsage

logger = logging.getLogger(__name__)


class TerritoryAlignmentSkill(BaseSkill):
    """Cluster retailers into territories using k-means."""

    def __init__(self):
        super().__init__()
        self.metadata = SkillMetadata(
            id="territory_alignment_poc",
            name="Territory Alignment POC",
            description="Assign retailers to territories using k-means clustering",
            category="analytics",
        )

    def apply(
        self,
        state: ProjectState,
        workspace_path: Path | None = None,
        intake_config: dict | None = None,
        **kwargs,
    ) -> SkillResult:
        """Apply the alignment skill.

        Args:
            state: Current project state
            workspace_path: Path to workspace root
            intake_config: Intake YAML configuration
            **kwargs: Additional arguments

        Returns:
            SkillResult with territory assignments and KPIs
        """
        logger.info("Starting territory alignment skill")

        # Resolve paths
        if not workspace_path:
            raise ValueError("workspace_path is required for territory alignment")

        workspace_path = Path(workspace_path)
        artifacts_path = workspace_path / "artifacts"
        artifacts_path.mkdir(parents=True, exist_ok=True)

        # Load scored retailers
        scored_path = artifacts_path / "retailers_midwest_scored.csv"
        if not scored_path.exists():
            raise FileNotFoundError(
                f"Scored retailers file not found at {scored_path}. "
                f"Run territory_scoring_poc skill first."
            )

        logger.info(f"Loading scored retailers from {scored_path}")
        df = pd.read_csv(scored_path)
        logger.info(f"Loaded {len(df)} scored retailers")

        # Get config
        config = intake_config or {}
        territory_config = config.get("territory", {})
        scoring_config = config.get("scoring", {})
        weights = scoring_config.get("weights", {})

        n_territories = territory_config.get("target_territories", 12)
        value_weight = weights.get("value_weight", 0.5)
        opportunity_weight = weights.get("opportunity_weight", 0.3)
        workload_weight = weights.get("workload_weight", 0.2)

        logger.info(f"Clustering into {n_territories} territories")
        logger.info(f"Weights: value={value_weight}, opp={opportunity_weight}, work={workload_weight}")

        # Add geographic coordinates
        df = add_coordinates_to_dataframe(df, zip_column="zip")

        # Filter out rows without coordinates
        df_with_coords = df[df["latitude"].notna() & df["longitude"].notna()].copy()
        if len(df_with_coords) == 0:
            raise ValueError("No retailers have valid coordinates for clustering")

        logger.info(f"{len(df_with_coords)} retailers have valid coordinates")

        # Compute composite score
        df_with_coords["composite_score"] = (
            value_weight * df_with_coords["RVS"]
            + opportunity_weight * df_with_coords["ROS"]
            + workload_weight * df_with_coords["RWS"]
        )

        # Prepare features for clustering
        # Use lat/lon and composite score
        features = df_with_coords[["latitude", "longitude", "composite_score"]].copy()

        # Scale features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Apply geographic weighting (lat/lon more important than score for geography)
        geo_weight = 2.0
        features_scaled[:, 0] *= geo_weight  # latitude
        features_scaled[:, 1] *= geo_weight  # longitude

        # Run k-means
        kmeans = KMeans(
            n_clusters=n_territories,
            random_state=42,
            n_init=10,
            max_iter=300,
        )
        df_with_coords["territory_id"] = kmeans.fit_predict(features_scaled)

        # Format territory IDs nicely (T01, T02, etc.)
        df_with_coords["territory_id"] = df_with_coords["territory_id"].apply(
            lambda x: f"T{x + 1:02d}"
        )

        # Compute per-territory KPIs
        kpis = self._compute_territory_kpis(df_with_coords)

        # Write outputs
        assignments_path = artifacts_path / "territory_assignments.csv"
        kpis_path = artifacts_path / "territory_kpis.csv"

        df_with_coords.to_csv(assignments_path, index=False)
        kpis.to_csv(kpis_path, index=False)

        logger.info(f"Wrote territory assignments to {assignments_path}")
        logger.info(f"Wrote territory KPIs to {kpis_path}")

        # Build result
        return SkillResult(
            skill_id=self.metadata.id,
            success=True,
            artifacts=[
                ArtifactInfo(
                    path=str(assignments_path),
                    hash=compute_file_hash(assignments_path),
                    size_bytes=assignments_path.stat().st_size,
                    artifact_type="csv",
                ),
                ArtifactInfo(
                    path=str(kpis_path),
                    hash=compute_file_hash(kpis_path),
                    size_bytes=kpis_path.stat().st_size,
                    artifact_type="csv",
                ),
            ],
            metadata={
                "retailer_count": len(df_with_coords),
                "territory_count": n_territories,
                "weights_used": {
                    "value": value_weight,
                    "opportunity": opportunity_weight,
                    "workload": workload_weight,
                },
                "kpi_summary": {
                    "avg_retailers_per_territory": len(df_with_coords) / n_territories,
                    "min_retailers": int(kpis["retailer_count"].min()),
                    "max_retailers": int(kpis["retailer_count"].max()),
                },
            },
            token_usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
        )

    def _compute_territory_kpis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute KPIs for each territory.

        Returns DataFrame with columns:
        - territory_id
        - retailer_count
        - total_revenue
        - avg_rvs, avg_ros, avg_rws
        - centroid_lat, centroid_lon
        - coverage_km (max distance from centroid)
        """
        kpis = []

        for territory_id in sorted(df["territory_id"].unique()):
            territory_df = df[df["territory_id"] == territory_id]

            # Basic counts
            retailer_count = len(territory_df)

            # Revenue (sum avg_revenue if available)
            total_revenue = territory_df["avg_revenue"].sum() if "avg_revenue" in territory_df else 0

            # Average scores
            avg_rvs = territory_df["RVS"].mean()
            avg_ros = territory_df["ROS"].mean()
            avg_rws = territory_df["RWS"].mean()
            avg_composite = territory_df["composite_score"].mean()

            # Geographic centroid
            centroid_lat = territory_df["latitude"].mean()
            centroid_lon = territory_df["longitude"].mean()

            # Coverage (max distance from centroid)
            max_distance = 0
            for _, row in territory_df.iterrows():
                dist = calculate_distance_km(
                    centroid_lat, centroid_lon,
                    row["latitude"], row["longitude"]
                )
                max_distance = max(max_distance, dist)

            kpis.append({
                "territory_id": territory_id,
                "retailer_count": retailer_count,
                "total_revenue": round(total_revenue, 2),
                "avg_rvs": round(avg_rvs, 3),
                "avg_ros": round(avg_ros, 3),
                "avg_rws": round(avg_rws, 3),
                "avg_composite": round(avg_composite, 3),
                "centroid_lat": round(centroid_lat, 4),
                "centroid_lon": round(centroid_lon, 4),
                "coverage_km": round(max_distance, 2),
            })

        return pd.DataFrame(kpis)
