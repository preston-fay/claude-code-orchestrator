"""
Territory Scoring Skill - Compute RVS/ROS/RWS for retailers.

This skill reads retailer data from the workspace, filters to IA/IL/IN,
computes value/opportunity/workload scores, and writes scored CSV to artifacts.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from orchestrator_v2.capabilities.skills.models import BaseSkill, SkillMetadata, SkillResult
from orchestrator_v2.engine.state_models import ArtifactInfo, ProjectState, TokenUsage


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

logger = logging.getLogger(__name__)


class TerritoryScoringSkill(BaseSkill):
    """Compute RVS/ROS/RWS scores for territory POC."""

    def __init__(self):
        super().__init__()
        self.metadata = SkillMetadata(
            id="territory_scoring_poc",
            name="Territory Scoring POC",
            description="Compute RVS/ROS/RWS scores for IA/IL/IN retailers",
            category="analytics",
        )

    def apply(
        self,
        state: ProjectState,
        workspace_path: Path | None = None,
        intake_config: dict | None = None,
        **kwargs,
    ) -> SkillResult:
        """Apply the scoring skill.

        Args:
            state: Current project state
            workspace_path: Path to workspace root
            intake_config: Intake YAML configuration
            **kwargs: Additional arguments

        Returns:
            SkillResult with scored CSV artifact
        """
        logger.info("Starting territory scoring skill")

        # Resolve paths
        if not workspace_path:
            raise ValueError("workspace_path is required for territory scoring")

        workspace_path = Path(workspace_path)
        data_path = workspace_path / "data"
        artifacts_path = workspace_path / "artifacts"
        artifacts_path.mkdir(parents=True, exist_ok=True)

        # Get config from intake
        config = intake_config or {}
        excel_filename = config.get("data", {}).get("retailers_excel", "Retailer_Segmentation_CROP.xlsx")

        # Handle relative paths - look in data/ folder by default
        if not excel_filename.startswith("/"):
            # First try data/ folder
            excel_path = data_path / excel_filename
            # If not found there, try workspace root as fallback
            if not excel_path.exists():
                excel_path = workspace_path / excel_filename
        else:
            excel_path = Path(excel_filename)

        if not excel_path.exists():
            raise FileNotFoundError(
                f"Retailer data file not found at {excel_path}. "
                f"Please place the Excel file in the workspace data directory."
            )

        # Load Excel
        logger.info(f"Loading retailer data from {excel_path}")
        df = pd.read_excel(excel_path)
        logger.info(f"Loaded {len(df)} rows")

        # Find state column (flexible naming)
        state_col = self._find_column(df, [
            "State", "state", "ST", "st",
            "static_entity_state",  # Corteva segmentation format
        ])
        if not state_col:
            available = ", ".join(df.columns[:20].tolist())
            raise ValueError(f"Could not find state column in Excel file. Available columns: {available}...")

        # Filter to IA, IL, IN
        states = config.get("territory", {}).get("states", ["IA", "IL", "IN"])
        df_filtered = df[df[state_col].str.upper().isin([s.upper() for s in states])].copy()
        logger.info(f"Filtered to {len(df_filtered)} retailers in {states}")

        if len(df_filtered) == 0:
            raise ValueError(f"No retailers found in states {states}")

        # Standardize column names for output
        df_scored = self._standardize_columns(df_filtered, state_col)

        # Get scoring config
        scoring_config = config.get("scoring", {})
        weights = scoring_config.get("weights", {})
        value_config = scoring_config.get("value", {})
        opportunity_config = scoring_config.get("opportunity", {})
        workload_config = scoring_config.get("workload", {})

        # Compute RVS (Retail Value Score)
        df_scored = self._compute_rvs(df_scored, df_filtered, value_config)

        # Compute ROS (Retail Opportunity Score)
        df_scored = self._compute_ros(df_scored, opportunity_config)

        # Compute RWS (Retail Workload Score)
        df_scored = self._compute_rws(df_scored, workload_config)

        # Write output
        output_path = artifacts_path / "retailers_midwest_scored.csv"
        df_scored.to_csv(output_path, index=False)
        logger.info(f"Wrote scored retailers to {output_path}")

        # Build result
        return SkillResult(
            skill_id=self.metadata.id,
            success=True,
            artifacts=[
                ArtifactInfo(
                    path=str(output_path),
                    hash=compute_file_hash(output_path),
                    size_bytes=output_path.stat().st_size,
                    artifact_type="csv",
                )
            ],
            metadata={
                "retailer_count": len(df_scored),
                "states": states,
                "rvs_min": float(df_scored["RVS"].min()),
                "rvs_max": float(df_scored["RVS"].max()),
                "ros_min": float(df_scored["ROS"].min()),
                "ros_max": float(df_scored["ROS"].max()),
                "rws_min": float(df_scored["RWS"].min()),
                "rws_max": float(df_scored["RWS"].max()),
            },
            token_usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
        )

    def _find_column(self, df: pd.DataFrame, candidates: list[str]) -> str | None:
        """Find first matching column from candidates."""
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def _standardize_columns(self, df: pd.DataFrame, state_col: str) -> pd.DataFrame:
        """Create standardized output DataFrame."""
        # Map potential column names to standard names
        column_mapping = {
            "retail_id": ["GLN", "Ship To", "ShipTo", "ID", "RetailID", "Retail_ID", "static_GLN", "R_INCA"],
            "retail_name": ["Name", "Retailer Name", "RetailerName", "Customer Name", "static_entity_name", "static_entity_dba_name"],
            "parent_org": ["Parent", "Parent Org", "ParentOrg", "Organization", "static_L5_Name"],
            "city": ["City", "CITY", "static_entity_city"],
            "zip": ["Zip", "ZIP", "Postal Code", "PostalCode", "static_entity_postal_code"],
            "segment": ["Segment", "SEGMENT", "Seg", "Segmentation", "Segment_Label", "segment_description"],
        }

        result = pd.DataFrame()

        # Find and map columns
        for std_name, candidates in column_mapping.items():
            col = self._find_column(df, candidates)
            if col:
                result[std_name] = df[col]
            else:
                result[std_name] = ""

        # State column
        result["state"] = df[state_col].str.upper()

        # Try to find revenue columns
        rev_cols = ["CY Rev", "PY Rev", "PPY Rev", "CY_Rev", "PY_Rev", "PPY_Rev",
                    "Revenue", "Sales", "Volume",
                    "sum_net_value", "sum_gross_value",  # Corteva format
                    "df_yoy_sales_2024", "df_yoy_sales_2023", "df_yoy_sales_2022"]
        for col in rev_cols:
            if col in df.columns:
                result[col.replace(" ", "_")] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return result

    def _compute_rvs(
        self,
        df_scored: pd.DataFrame,
        df_original: pd.DataFrame,
        config: dict,
    ) -> pd.DataFrame:
        """Compute Retail Value Score (RVS)."""
        # Find revenue columns - try multiple formats
        sales_cols = config.get("sales_columns", [
            "CY Rev", "PY Rev", "PPY Rev",
            "sum_net_value",  # Corteva primary revenue
            "df_yoy_sales_2024", "df_yoy_sales_2023", "df_yoy_sales_2022"
        ])

        # Try to find actual revenue data
        revenue_values = []
        for _, row in df_original.iterrows():
            rev_sum = 0
            count = 0
            for col in sales_cols:
                if col in df_original.columns:
                    val = pd.to_numeric(row.get(col, 0), errors="coerce")
                    if pd.notna(val) and val > 0:
                        rev_sum += val
                        count += 1
            avg_rev = rev_sum / max(count, 1)
            revenue_values.append(avg_rev)

        df_scored["avg_revenue"] = revenue_values

        # Normalize to 0-1 using percentile rank
        if df_scored["avg_revenue"].max() > df_scored["avg_revenue"].min():
            df_scored["RVS"] = (
                df_scored["avg_revenue"].rank(pct=True)
            )
        else:
            df_scored["RVS"] = 0.5

        return df_scored

    def _compute_ros(self, df_scored: pd.DataFrame, config: dict) -> pd.DataFrame:
        """Compute Retail Opportunity Score (ROS)."""
        segment_field = config.get("segment_field", "segment")

        # Map segments to opportunity scores
        segment_opportunity = {
            "elite": 0.9,
            "core": 0.7,
            "core plus": 0.75,
            "core+": 0.75,
            "explorer": 0.5,
            "standard": 0.6,
            "basic": 0.4,
            "low": 0.3,
        }

        ros_values = []
        for _, row in df_scored.iterrows():
            segment = str(row.get(segment_field, "")).lower().strip()
            # Find best match
            score = 0.5  # Default
            for key, val in segment_opportunity.items():
                if key in segment:
                    score = val
                    break
            ros_values.append(score)

        df_scored["ROS"] = ros_values
        return df_scored

    def _compute_rws(self, df_scored: pd.DataFrame, config: dict) -> pd.DataFrame:
        """Compute Retail Workload Score (RWS)."""
        # Workload is combination of segment complexity and value
        # Higher value + complex segment = higher workload

        rws_values = []
        for _, row in df_scored.iterrows():
            # Base workload from segment
            segment = str(row.get("segment", "")).lower()
            if "elite" in segment:
                base = 0.8
            elif "core" in segment:
                base = 0.6
            elif "explorer" in segment:
                base = 0.4
            else:
                base = 0.5

            # Adjust by value (high value = more attention needed)
            rvs = row.get("RVS", 0.5)
            workload = 0.6 * base + 0.4 * rvs

            rws_values.append(workload)

        df_scored["RWS"] = rws_values
        return df_scored
