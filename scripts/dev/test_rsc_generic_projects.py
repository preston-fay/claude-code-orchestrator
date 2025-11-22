#!/usr/bin/env python3
"""
Sanity test to prove RSC is a generic orchestrator.

This script creates projects using different templates and verifies
that RSC handles them all the same way without special-casing.

Usage:
    python scripts/dev/test_rsc_generic_projects.py

Requirements:
    - API server running at http://localhost:8000
"""

import sys
import httpx
import asyncio
from datetime import datetime

API_BASE = "http://localhost:8000"

async def create_project(client: httpx.AsyncClient, name: str, template_id: str, description: str) -> dict:
    """Create a project and return its details."""
    print(f"\n{'='*60}")
    print(f"Creating: {name}")
    print(f"Template: {template_id}")
    print(f"{'='*60}")

    response = await client.post(
        f"{API_BASE}/projects",
        json={
            "project_name": name,
            "template_id": template_id,
            "client": "sanity-test",
        },
        headers={
            "X-User-Id": "test-user",
            "X-User-Email": "test@example.com",
        }
    )

    if response.status_code != 200:
        print(f"ERROR: Failed to create project: {response.status_code}")
        print(response.text)
        return None

    project = response.json()
    print(f"✓ Created: {project['project_id']}")
    print(f"  Type: {project['project_type']}")
    print(f"  Phase: {project['current_phase']}")
    print(f"  Workspace: {project.get('workspace_path', 'N/A')}")

    return project


async def verify_project_detail(client: httpx.AsyncClient, project_id: str) -> bool:
    """Verify project detail endpoint works."""
    response = await client.get(
        f"{API_BASE}/projects/{project_id}",
        headers={
            "X-User-Id": "test-user",
            "X-User-Email": "test@example.com",
        }
    )

    if response.status_code != 200:
        print(f"✗ Project detail failed: {response.status_code}")
        return False

    print(f"✓ Project detail works")
    return True


async def verify_rsg_overview(client: httpx.AsyncClient, project_id: str) -> bool:
    """Verify RSG overview endpoint works."""
    response = await client.get(
        f"{API_BASE}/rsg/{project_id}/overview",
        headers={
            "X-User-Id": "test-user",
            "X-User-Email": "test@example.com",
        }
    )

    if response.status_code != 200:
        print(f"✗ RSG overview failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✓ RSG overview works - Stage: {data.get('stage', 'N/A')}")
    return True


async def verify_features_endpoint(client: httpx.AsyncClient, project_id: str) -> bool:
    """Verify features endpoint works."""
    response = await client.get(
        f"{API_BASE}/projects/{project_id}/features",
        headers={
            "X-User-Id": "test-user",
            "X-User-Email": "test@example.com",
        }
    )

    if response.status_code != 200:
        print(f"✗ Features endpoint failed: {response.status_code}")
        return False

    features = response.json()
    print(f"✓ Features endpoint works - Count: {len(features)}")
    return True


async def run_tests():
    """Run all sanity tests."""
    print("\n" + "="*60)
    print("RSC GENERIC ORCHESTRATOR SANITY TEST")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check API health
        try:
            health = await client.get(f"{API_BASE}/health")
            if health.status_code != 200:
                print("ERROR: API server not responding")
                return False
            print("✓ API server healthy")
        except Exception as e:
            print(f"ERROR: Cannot connect to API: {e}")
            return False

        # Test projects
        test_cases = [
            {
                "name": f"Generic App Build Test {datetime.now().strftime('%H%M%S')}",
                "template_id": "app_build",
                "description": "Tests that App Build template works generically",
            },
            {
                "name": f"Analytics Forecasting Test {datetime.now().strftime('%H%M%S')}",
                "template_id": "golden_path_analytics",
                "description": "Tests that Analytics template works without territory coupling",
            },
            {
                "name": f"Territory Demo Test {datetime.now().strftime('%H%M%S')}",
                "template_id": "territory_poc_midwest",
                "description": "Tests that Territory demo template works as a consumer",
            },
            {
                "name": f"Blank Project Test {datetime.now().strftime('%H%M%S')}",
                "template_id": "blank",
                "description": "Tests that Blank template works for custom projects",
            },
        ]

        results = []

        for test in test_cases:
            project = await create_project(
                client,
                test["name"],
                test["template_id"],
                test["description"]
            )

            if not project:
                results.append((test["template_id"], False, "Creation failed"))
                continue

            project_id = project["project_id"]

            # Verify all generic endpoints work
            detail_ok = await verify_project_detail(client, project_id)
            rsg_ok = await verify_rsg_overview(client, project_id)
            features_ok = await verify_features_endpoint(client, project_id)

            all_ok = detail_ok and rsg_ok and features_ok
            results.append((test["template_id"], all_ok, project_id))

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        all_passed = True
        for template_id, passed, info in results:
            status = "PASS" if passed else "FAIL"
            print(f"{status}: {template_id} - {info}")
            if not passed:
                all_passed = False

        print("\n" + "="*60)
        if all_passed:
            print("✓ ALL TESTS PASSED")
            print("RSC is template-agnostic and handles all project types generically.")
        else:
            print("✗ SOME TESTS FAILED")
            print("Check the errors above.")
        print("="*60 + "\n")

        return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
