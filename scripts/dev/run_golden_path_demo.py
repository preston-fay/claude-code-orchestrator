#!/usr/bin/env python3
"""
Golden Path Demo - Run a canonical project through Ready-Set-Code.

This script demonstrates the full orchestration flow by:
1. Creating a new project via the API
2. Running Ready → Set → Go stages
3. Showing final RSG overview

Usage:
    python scripts/dev/run_golden_path_demo.py

Prerequisites:
    - API server running: python scripts/dev/run_api_server.py
    - LLM provider configured in UI Settings
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

# Configuration
API_URL = os.getenv("ORCHESTRATOR_API_URL", "http://localhost:8000")
PROJECT_NAME = "Golden Path - Customer Demand Forecast"
PROJECT_DESCRIPTION = "Canonical example demonstrating Ready-Set-Code end-to-end orchestration"
CLIENT = "kearney-default"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log(message: str, color: str = ""):
    """Print a log message with optional color."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if color:
        print(f"{color}[{timestamp}] {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {message}")


def log_success(message: str):
    log(f"✓ {message}", Colors.GREEN)


def log_error(message: str):
    log(f"✗ {message}", Colors.FAIL)


def log_info(message: str):
    log(f"→ {message}", Colors.CYAN)


def log_header(message: str):
    print()
    log(f"{Colors.BOLD}{message}{Colors.ENDC}", Colors.HEADER)
    print("=" * 60)


def check_api_health():
    """Check if the API is reachable."""
    log_info("Checking API health...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            log_success(f"API is healthy at {API_URL}")
            return True
        else:
            log_error(f"API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        log_error(f"Cannot connect to API at {API_URL}")
        log_info("Make sure the API server is running:")
        log_info("  python scripts/dev/run_api_server.py")
        return False
    except Exception as e:
        log_error(f"Error checking API: {e}")
        return False


def create_project():
    """Create a new Golden Path project."""
    log_info(f"Creating project: {PROJECT_NAME}")

    payload = {
        "project_name": PROJECT_NAME,
        "client": CLIENT,
        "metadata": {
            "description": PROJECT_DESCRIPTION,
            "type": "analytics_forecasting",
            "domain": "retail",
            "golden_path": True,
            "intake_template": "examples/golden_path/intake_analytics_forecasting.yaml",
        }
    }

    try:
        response = requests.post(
            f"{API_URL}/projects",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 201:
            project = response.json()
            log_success(f"Project created: {project['project_id']}")
            return project
        else:
            log_error(f"Failed to create project: {response.status_code}")
            log_error(response.text)
            return None
    except Exception as e:
        log_error(f"Error creating project: {e}")
        return None


def run_rsg_stage(project_id: str, stage: str):
    """Run a single RSG stage."""
    stage_names = {
        "ready": "Ready (Planning + Architecture)",
        "set": "Set (Data + Development)",
        "go": "Go (Development + QA + Documentation)"
    }

    log_info(f"Starting {stage_names.get(stage, stage)}...")

    try:
        response = requests.post(
            f"{API_URL}/rsg/{project_id}/{stage}/start",
            timeout=120  # RSG stages can take time
        )

        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")

            if status == "completed":
                log_success(f"{stage.capitalize()} stage completed")
            elif status == "running":
                log_info(f"{stage.capitalize()} stage is running...")
            else:
                log_info(f"{stage.capitalize()} stage status: {status}")

            return result
        else:
            log_error(f"Failed to start {stage} stage: {response.status_code}")
            try:
                error_detail = response.json().get("detail", response.text)
                log_error(f"  {error_detail}")
            except:
                log_error(f"  {response.text}")
            return None
    except requests.exceptions.Timeout:
        log_error(f"Timeout waiting for {stage} stage")
        return None
    except Exception as e:
        log_error(f"Error running {stage} stage: {e}")
        return None


def get_rsg_overview(project_id: str):
    """Get the RSG overview for a project."""
    try:
        response = requests.get(
            f"{API_URL}/rsg/{project_id}/overview",
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            log_error(f"Failed to get RSG overview: {response.status_code}")
            return None
    except Exception as e:
        log_error(f"Error getting RSG overview: {e}")
        return None


def get_project_events(project_id: str, limit: int = 10):
    """Get recent events for a project."""
    try:
        response = requests.get(
            f"{API_URL}/projects/{project_id}/events?limit={limit}",
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def print_overview(overview: dict):
    """Print a formatted RSG overview."""
    log_header("RSG Overview")

    stages = ["ready", "set", "go"]
    for stage in stages:
        stage_data = overview.get(stage, {})
        status = stage_data.get("status", "pending")
        phases = stage_data.get("phases_completed", [])

        # Status indicator
        if status == "completed":
            indicator = f"{Colors.GREEN}●{Colors.ENDC}"
        elif status == "running":
            indicator = f"{Colors.CYAN}◐{Colors.ENDC}"
        else:
            indicator = f"{Colors.WARNING}○{Colors.ENDC}"

        print(f"  {indicator} {stage.upper()}: {status}")
        if phases:
            print(f"      Phases: {', '.join(phases)}")

    print()


def print_recent_events(events: list):
    """Print recent events."""
    if not events:
        return

    log_header("Recent Events")
    for event in events[:5]:
        event_type = event.get("event_type", "unknown")
        message = event.get("message", "")
        timestamp = event.get("timestamp", "")

        # Color based on event type
        if "completed" in event_type or "passed" in event_type:
            color = Colors.GREEN
        elif "failed" in event_type or "error" in event_type:
            color = Colors.FAIL
        elif "started" in event_type:
            color = Colors.CYAN
        else:
            color = ""

        time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
        print(f"  {color}[{time_str}] {message}{Colors.ENDC}")

    print()


def main():
    """Run the Golden Path demo."""
    print()
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         READY-SET-CODE: Golden Path Demo                   ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    # Step 1: Check API health
    log_header("Step 1: Verify API")
    if not check_api_health():
        sys.exit(1)

    # Step 2: Create project
    log_header("Step 2: Create Project")
    project = create_project()
    if not project:
        sys.exit(1)

    project_id = project["project_id"]

    # Step 3: Run RSG stages
    log_header("Step 3: Run Ready-Set-Go")

    # Ready stage
    result = run_rsg_stage(project_id, "ready")
    if not result:
        log_error("Ready stage failed. Check API logs for details.")
        # Continue anyway to show overview

    time.sleep(1)  # Brief pause between stages

    # Set stage
    result = run_rsg_stage(project_id, "set")
    if not result:
        log_error("Set stage failed. Check API logs for details.")

    time.sleep(1)

    # Go stage
    result = run_rsg_stage(project_id, "go")
    if not result:
        log_error("Go stage failed. Check API logs for details.")

    # Step 4: Show results
    log_header("Step 4: Results")

    overview = get_rsg_overview(project_id)
    if overview:
        print_overview(overview)

    events = get_project_events(project_id, limit=10)
    print_recent_events(events)

    # Final summary
    log_header("Summary")
    log_success(f"Project ID: {project_id}")
    log_success(f"Project Name: {PROJECT_NAME}")
    log_info(f"API URL: {API_URL}")
    log_info(f"View in UI: http://localhost:5173/projects/{project_id}")

    print()
    print(f"{Colors.CYAN}Next steps:{Colors.ENDC}")
    print("  1. Open the UI at http://localhost:5173")
    print("  2. Click on the Golden Path project")
    print("  3. View Run Activity panel for execution details")
    print("  4. Check phase statuses and checkpoints")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
