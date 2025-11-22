#!/usr/bin/env python3
"""
Orchestrator Deployment Verification Script

Verifies that the Orchestrator API is running correctly after deployment
to AWS App Runner or any other hosting environment.

Usage:
    python scripts/verify_deployment.py --url https://xxxxx.awsapprunner.com

Requirements:
    - Python 3.7+
    - No external dependencies (stdlib only)
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import Tuple, Optional, Any


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def colorize(text: str, color: str) -> str:
    """Add color to text if stdout is a terminal."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.END}"
    return text


def make_request(
    url: str,
    method: str = "GET",
    data: Optional[dict] = None,
    timeout: int = 30
) -> Tuple[int, Any]:
    """Make an HTTP request and return (status_code, response_data)."""
    headers = {"Content-Type": "application/json"}

    if data:
        body = json.dumps(data).encode('utf-8')
    else:
        body = None

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            content = response.read().decode('utf-8')
            try:
                return status, json.loads(content)
            except json.JSONDecodeError:
                return status, content
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        try:
            return e.code, json.loads(content)
        except json.JSONDecodeError:
            return e.code, content
    except urllib.error.URLError as e:
        raise ConnectionError(f"Connection failed: {e.reason}")


def print_header(url: str):
    """Print the verification header."""
    print()
    print(colorize("Orchestrator Deployment Verification", Colors.BOLD))
    print("=" * 45)
    print(f"Target: {colorize(url, Colors.BLUE)}")
    print()


def print_result(step: str, total: int, current: int, success: bool, detail: str = ""):
    """Print a test step result."""
    status = colorize("OK", Colors.GREEN) if success else colorize("FAILED", Colors.RED)
    padding = "." * (30 - len(step))
    print(f"[{current}/{total}] {step}{padding} {status}")
    if detail and not success:
        print(f"      Error: {detail}")


def print_footer(success: bool):
    """Print the verification footer."""
    print()
    print("=" * 45)
    if success:
        print(colorize("VERIFICATION PASSED", Colors.GREEN + Colors.BOLD))
        print("All endpoints responding correctly")
    else:
        print(colorize("VERIFICATION FAILED", Colors.RED + Colors.BOLD))
        print("Check App Runner logs for details")
    print("=" * 45)
    print()


def verify_health(base_url: str) -> Tuple[bool, str]:
    """Verify the health endpoint."""
    try:
        status, data = make_request(f"{base_url}/health")
        if status == 200 and isinstance(data, dict) and data.get("status") == "healthy":
            return True, ""
        return False, f"Unexpected response: {data}"
    except ConnectionError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def verify_create_project(base_url: str) -> Tuple[bool, str, Optional[str]]:
    """Create a test project and return (success, error, project_id)."""
    try:
        status, data = make_request(
            f"{base_url}/projects",
            method="POST",
            data={
                "name": "DeploymentTest",
                "description": "Automated deployment verification"
            }
        )
        if status in (200, 201) and isinstance(data, dict):
            project_id = data.get("project_id") or data.get("id")
            if project_id:
                return True, "", project_id
            return False, f"No project_id in response: {data}", None
        return False, f"Status {status}: {data}", None
    except ConnectionError as e:
        return False, str(e), None
    except Exception as e:
        return False, str(e), None


def verify_start_ready(base_url: str, project_id: str) -> Tuple[bool, str]:
    """Start the Ready stage for a project."""
    try:
        status, data = make_request(
            f"{base_url}/rsg/{project_id}/ready/start",
            method="POST"
        )
        if status in (200, 201, 202):
            return True, ""
        return False, f"Status {status}: {data}"
    except ConnectionError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def verify_get_overview(base_url: str, project_id: str) -> Tuple[bool, str]:
    """Get the RSG overview for a project."""
    try:
        status, data = make_request(f"{base_url}/rsg/{project_id}/overview")
        if status == 200 and isinstance(data, dict):
            return True, ""
        return False, f"Status {status}: {data}"
    except ConnectionError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def main():
    """Main verification routine."""
    parser = argparse.ArgumentParser(
        description="Verify Orchestrator API deployment"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="App Runner URL (e.g., https://xxxxx.awsapprunner.com)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )

    args = parser.parse_args()

    # Normalize URL (remove trailing slash)
    base_url = args.url.rstrip("/")

    print_header(base_url)

    all_passed = True
    project_id = None

    # Step 1: Health check
    success, error = verify_health(base_url)
    print_result("Health Check", 4, 1, success, error)
    if not success:
        all_passed = False

    # Step 2: Create project
    if all_passed:
        success, error, project_id = verify_create_project(base_url)
        detail = f"(id: {project_id[:8]}...)" if success and project_id else error
        print_result("Create Project", 4, 2, success, error if not success else "")
        if success and project_id:
            print(f"      Project ID: {project_id[:8]}...")
        if not success:
            all_passed = False
    else:
        print_result("Create Project", 4, 2, False, "Skipped due to previous failure")
        all_passed = False

    # Step 3: Start Ready stage
    if all_passed and project_id:
        success, error = verify_start_ready(base_url, project_id)
        print_result("Start Ready Stage", 4, 3, success, error)
        if not success:
            all_passed = False
    else:
        print_result("Start Ready Stage", 4, 3, False, "Skipped due to previous failure")
        all_passed = False

    # Step 4: Get RSG overview
    if all_passed and project_id:
        success, error = verify_get_overview(base_url, project_id)
        print_result("Get RSG Overview", 4, 4, success, error)
        if not success:
            all_passed = False
    else:
        print_result("Get RSG Overview", 4, 4, False, "Skipped due to previous failure")
        all_passed = False

    print_footer(all_passed)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
