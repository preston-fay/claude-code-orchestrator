#!/usr/bin/env python3
"""
Territory POC Demo Runner

Sets up workspace with sample data and runs the territory scoring
and clustering pipeline to demonstrate the Territory POC functionality.

Usage:
    python scripts/dev/run_territory_poc_demo.py

Prerequisites:
    - Place your Retailer_Segmentation_CROP.xlsx file in:
      /home/user/workspaces/territory_poc/data/

    OR use the --generate-sample flag to create sample data.
"""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def setup_workspace(workspace_path: Path) -> None:
    """Create workspace directory structure."""
    logger.info(f"Setting up workspace at {workspace_path}")

    # Create directories
    (workspace_path / "data").mkdir(parents=True, exist_ok=True)
    (workspace_path / "artifacts").mkdir(parents=True, exist_ok=True)
    (workspace_path / "logs").mkdir(parents=True, exist_ok=True)

    logger.info("Workspace directories created")


def generate_sample_data(workspace_path: Path, num_retailers: int = 200) -> None:
    """Generate sample retailer data for demo purposes."""
    logger.info(f"Generating sample data with {num_retailers} retailers")

    # Sample cities by state
    cities = {
        "IA": ["Des Moines", "Cedar Rapids", "Davenport", "Sioux City", "Iowa City",
               "Waterloo", "Council Bluffs", "Ames", "Dubuque", "West Des Moines"],
        "IL": ["Chicago", "Aurora", "Naperville", "Joliet", "Rockford",
               "Springfield", "Peoria", "Elgin", "Champaign", "Waukegan"],
        "IN": ["Indianapolis", "Fort Wayne", "Evansville", "South Bend", "Carmel",
               "Fishers", "Bloomington", "Hammond", "Gary", "Lafayette"],
    }

    # Sample ZIP codes by state (3-digit prefixes)
    zips = {
        "IA": ["500", "501", "502", "503", "504", "505", "506", "507", "508", "509"],
        "IL": ["600", "601", "602", "603", "604", "605", "606", "607", "608", "609"],
        "IN": ["460", "461", "462", "463", "464", "465", "466", "467", "468", "469"],
    }

    # Segments
    segments = ["Elite", "Core Plus", "Core", "Explorer"]
    segment_weights = [0.1, 0.2, 0.4, 0.3]

    # Parent organizations
    parents = [
        "AgriCorp", "FarmSupply Inc", "Midwest Ag", "Prairie Partners",
        "Heartland Co-op", "Central States AG", "Green Valley", "Harvest Supply",
        "Crop Solutions", "Independent"
    ]

    # Generate data
    np.random.seed(42)

    data = []
    for i in range(num_retailers):
        state = np.random.choice(["IA", "IL", "IN"], p=[0.33, 0.34, 0.33])
        city = np.random.choice(cities[state])
        zip_prefix = np.random.choice(zips[state])
        zip_code = f"{zip_prefix}{np.random.randint(10, 99)}"

        segment = np.random.choice(segments, p=segment_weights)
        parent = np.random.choice(parents)

        # Revenue based on segment
        if segment == "Elite":
            cy_rev = np.random.uniform(500000, 2000000)
        elif segment == "Core Plus":
            cy_rev = np.random.uniform(200000, 600000)
        elif segment == "Core":
            cy_rev = np.random.uniform(50000, 250000)
        else:
            cy_rev = np.random.uniform(10000, 75000)

        # Historical revenue with some variance
        py_rev = cy_rev * np.random.uniform(0.85, 1.05)
        ppy_rev = cy_rev * np.random.uniform(0.75, 1.0)

        data.append({
            "GLN": f"GLN{100000 + i}",
            "Name": f"{city} {parent.split()[0]} #{i + 1}",
            "Parent Org": parent,
            "City": city,
            "State": state,
            "Zip": zip_code,
            "Segment": segment,
            "CY Rev": round(cy_rev, 2),
            "PY Rev": round(py_rev, 2),
            "PPY Rev": round(ppy_rev, 2),
        })

    df = pd.DataFrame(data)

    # Write to Excel
    output_path = workspace_path / "data" / "Retailer_Segmentation_CROP.xlsx"
    df.to_excel(output_path, index=False)
    logger.info(f"Generated sample data: {output_path}")
    logger.info(f"  - {len(df)} retailers")
    logger.info(f"  - States: {df['State'].value_counts().to_dict()}")
    logger.info(f"  - Segments: {df['Segment'].value_counts().to_dict()}")


def copy_intake_config(workspace_path: Path) -> None:
    """Copy intake YAML to workspace."""
    source = project_root / "examples" / "territory_poc" / "intake_territory_poc.yaml"
    dest = workspace_path / "intake.yaml"

    if source.exists():
        shutil.copy(source, dest)
        logger.info(f"Copied intake config to {dest}")
    else:
        logger.warning(f"Intake config not found at {source}")


def run_territory_pipeline(workspace_path: Path) -> None:
    """Run the territory scoring and clustering pipeline."""
    import yaml
    from orchestrator_v2.capabilities.skills.territory_poc import (
        TerritoryScoringSkill,
        TerritoryAlignmentSkill,
    )
    from orchestrator_v2.engine.state_models import ProjectState

    # Load intake config
    intake_path = workspace_path / "intake.yaml"
    if intake_path.exists():
        with open(intake_path) as f:
            intake_config = yaml.safe_load(f)
    else:
        intake_config = {
            "territory": {
                "target_territories": 12,
                "states": ["IA", "IL", "IN"],
            },
            "scoring": {
                "weights": {
                    "value_weight": 0.5,
                    "opportunity_weight": 0.3,
                    "workload_weight": 0.2,
                },
            },
        }

    # Create project state
    state = ProjectState(
        project_id="territory-poc-demo",
        run_id="demo-run",
        project_name="Territory POC Demo",
    )

    # Run scoring
    logger.info("=" * 60)
    logger.info("Running Territory Scoring Skill")
    logger.info("=" * 60)

    scoring_skill = TerritoryScoringSkill()
    scoring_result = scoring_skill.apply(
        state=state,
        workspace_path=workspace_path,
        intake_config=intake_config,
    )

    if scoring_result.success:
        logger.info(f"Scoring complete!")
        logger.info(f"  - Retailers scored: {scoring_result.metadata.get('retailer_count')}")
        logger.info(f"  - RVS range: {scoring_result.metadata.get('rvs_min'):.3f} - {scoring_result.metadata.get('rvs_max'):.3f}")
        logger.info(f"  - ROS range: {scoring_result.metadata.get('ros_min'):.3f} - {scoring_result.metadata.get('ros_max'):.3f}")
        logger.info(f"  - RWS range: {scoring_result.metadata.get('rws_min'):.3f} - {scoring_result.metadata.get('rws_max'):.3f}")
    else:
        logger.error(f"Scoring failed: {scoring_result.error}")
        return

    # Run clustering
    logger.info("")
    logger.info("=" * 60)
    logger.info("Running Territory Alignment Skill")
    logger.info("=" * 60)

    alignment_skill = TerritoryAlignmentSkill()
    alignment_result = alignment_skill.apply(
        state=state,
        workspace_path=workspace_path,
        intake_config=intake_config,
    )

    if alignment_result.success:
        logger.info(f"Alignment complete!")
        logger.info(f"  - Retailers assigned: {alignment_result.metadata.get('retailer_count')}")
        logger.info(f"  - Territories created: {alignment_result.metadata.get('territory_count')}")
        kpi_summary = alignment_result.metadata.get('kpi_summary', {})
        logger.info(f"  - Avg retailers/territory: {kpi_summary.get('avg_retailers_per_territory', 0):.1f}")
        logger.info(f"  - Range: {kpi_summary.get('min_retailers', 0)} - {kpi_summary.get('max_retailers', 0)}")
    else:
        logger.error(f"Alignment failed: {alignment_result.error}")
        return

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Territory POC Demo Complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Output artifacts:")
    for artifact in scoring_result.artifacts + alignment_result.artifacts:
        logger.info(f"  - {artifact.name}: {artifact.path}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Start the API server: uvicorn orchestrator_v2.api.server:app --reload")
    logger.info("  2. Start the UI: cd rsg-ui && npm run dev")
    logger.info("  3. Navigate to http://localhost:5173/territory-poc")
    logger.info(f"  4. Enter workspace path: {workspace_path}")
    logger.info("  5. Load results or re-run with different parameters")


def main():
    parser = argparse.ArgumentParser(
        description="Run Territory POC Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default="/home/user/workspaces/territory_poc",
        help="Workspace path (default: /home/user/workspaces/territory_poc)",
    )
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Generate sample retailer data for demo",
    )
    parser.add_argument(
        "--num-retailers",
        type=int,
        default=200,
        help="Number of retailers to generate (default: 200)",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Only setup workspace, don't run pipeline",
    )

    args = parser.parse_args()
    workspace_path = Path(args.workspace)

    logger.info("Territory POC Demo Runner")
    logger.info("=" * 60)

    # Setup workspace
    setup_workspace(workspace_path)

    # Copy intake config
    copy_intake_config(workspace_path)

    # Check for data or generate sample
    data_file = workspace_path / "data" / "Retailer_Segmentation_CROP.xlsx"
    if not data_file.exists():
        if args.generate_sample:
            generate_sample_data(workspace_path, args.num_retailers)
        else:
            logger.error(f"Data file not found: {data_file}")
            logger.error("Either:")
            logger.error(f"  1. Place your Retailer_Segmentation_CROP.xlsx in {workspace_path / 'data'}")
            logger.error("  2. Use --generate-sample to create sample data")
            sys.exit(1)
    else:
        logger.info(f"Using existing data file: {data_file}")

    # Run pipeline
    if not args.skip_run:
        run_territory_pipeline(workspace_path)
    else:
        logger.info("Skipping pipeline run (--skip-run)")
        logger.info(f"Workspace ready at: {workspace_path}")


if __name__ == "__main__":
    main()
