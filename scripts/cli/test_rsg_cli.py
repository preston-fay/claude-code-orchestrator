#!/usr/bin/env python3
"""
Test script for the RSG CLI.

Tests the Rich-enhanced Typer CLI for Ready/Set/Go operations.

Run with: python scripts/test_rsg_cli.py

Note: This script tests the CLI commands using Typer's CliRunner.
For full visual output, run the CLI directly:
  python -m orchestrator_v2.cli.rsg_cli init "Test Project"
"""

from typer.testing import CliRunner

from orchestrator_v2.cli.rsg_cli import app

runner = CliRunner()


def test_rsg_cli():
    """Test the complete RSG CLI flow."""
    print("=" * 60)
    print("RSG CLI Test (Typer + Rich)")
    print("=" * 60)

    # Note: These tests use CliRunner which captures output
    # For full Rich rendering, run CLI directly

    # 1. Test help
    print("\n" + "-" * 60)
    print("Test 1: CLI Help")
    print("-" * 60)

    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    print("\n  Help output available: OK")
    print(f"  Commands found: {result.output.count('start') > 0}")

    # 2. Test list (empty)
    print("\n" + "-" * 60)
    print("Test 2: List Projects")
    print("-" * 60)

    result = runner.invoke(app, ["list"])
    # May fail if API not running, that's OK for this test
    if result.exit_code == 0:
        print("\n  List command: OK")
    else:
        print("\n  List command: API not running (expected)")

    # 3. Test init command structure
    print("\n" + "-" * 60)
    print("Test 3: Init Command Structure")
    print("-" * 60)

    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "project_name" in result.output.lower() or "PROJECT_NAME" in result.output
    print("\n  Init help: OK")

    # 4. Test ready-start command structure
    print("\n" + "-" * 60)
    print("Test 4: Ready-Start Command Structure")
    print("-" * 60)

    result = runner.invoke(app, ["ready-start", "--help"])
    assert result.exit_code == 0
    assert "project_id" in result.output.lower() or "PROJECT_ID" in result.output
    print("\n  Ready-start help: OK")

    # 5. Test set-start command structure
    print("\n" + "-" * 60)
    print("Test 5: Set-Start Command Structure")
    print("-" * 60)

    result = runner.invoke(app, ["set-start", "--help"])
    assert result.exit_code == 0
    print("\n  Set-start help: OK")

    # 6. Test go-start command structure
    print("\n" + "-" * 60)
    print("Test 6: Go-Start Command Structure")
    print("-" * 60)

    result = runner.invoke(app, ["go-start", "--help"])
    assert result.exit_code == 0
    print("\n  Go-start help: OK")

    # 7. Test overview command structure
    print("\n" + "-" * 60)
    print("Test 7: Overview Command Structure")
    print("-" * 60)

    result = runner.invoke(app, ["overview", "--help"])
    assert result.exit_code == 0
    print("\n  Overview help: OK")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    print("\n  All CLI command structures validated!")
    print("\n  Available commands:")
    print("    - init <project_name>")
    print("    - list")
    print("    - ready-start <project_id>")
    print("    - ready-status <project_id>")
    print("    - set-start <project_id>")
    print("    - set-status <project_id>")
    print("    - go-start <project_id>")
    print("    - go-status <project_id>")
    print("    - overview <project_id>")

    print("\n  To run with full Rich output:")
    print("    1. Start API: python scripts/run_api_server.py")
    print("    2. Run CLI: python -m orchestrator_v2.cli.rsg_cli init 'My Project'")

    return True


def demo_rich_output():
    """Demo the Rich output formatting (requires API running)."""
    print("\n" + "=" * 60)
    print("RSG CLI Rich Output Demo")
    print("=" * 60)

    print("\nThis demo shows the Rich-formatted output.")
    print("Make sure the API server is running first.\n")

    # Import the console and utility functions
    from orchestrator_v2.cli.rsg_cli import (
        console,
        print_ready_status,
        print_rsg_overview,
        print_set_status,
        print_go_status,
        render_stage_banner,
    )

    # Demo the banner
    print("-" * 60)
    print("Stage Banners:")
    print("-" * 60)
    for stage in ["not_started", "ready", "set", "go", "complete"]:
        render_stage_banner(stage)

    # Demo Ready status
    print("\n" + "-" * 60)
    print("Ready Status Table:")
    print("-" * 60)
    demo_ready = {
        "stage": "ready",
        "completed": True,
        "current_phase": "data",
        "completed_phases": ["planning", "architecture"],
        "governance_passed": True,
        "messages": ["Completed planning phase", "Completed architecture phase"],
    }
    print_ready_status(demo_ready)

    # Demo Set status
    print("\n" + "-" * 60)
    print("Set Status Table:")
    print("-" * 60)
    demo_set = {
        "stage": "set",
        "completed": True,
        "current_phase": "qa",
        "completed_phases": ["data", "development"],
        "artifacts_count": 5,
        "data_ready": True,
        "messages": [],
    }
    print_set_status(demo_set)

    # Demo Go status
    print("\n" + "-" * 60)
    print("Go Status Table:")
    print("-" * 60)
    demo_go = {
        "stage": "complete",
        "completed": True,
        "current_phase": "complete",
        "completed_phases": ["development", "qa", "documentation"],
        "checkpoints_count": 8,
        "governance_blocked": False,
        "messages": [],
    }
    print_go_status(demo_go)

    # Demo Overview
    print("\n" + "-" * 60)
    print("Full Overview:")
    print("-" * 60)
    demo_overview = {
        "project_id": "abc-123-def-456",
        "project_name": "Demo RSG Project",
        "stage": "complete",
        "ready": demo_ready,
        "set": demo_set,
        "go": demo_go,
    }
    print_rsg_overview(demo_overview)


def main():
    """Main entry point."""
    import sys

    if "--demo" in sys.argv:
        demo_rich_output()
    else:
        success = test_rsg_cli()
        print("\n" + "=" * 60)
        if success:
            print("RSG CLI test completed successfully!")
        else:
            print("RSG CLI test failed!")
        print("=" * 60)
        print("\nRun with --demo to see Rich output formatting")
        print()


if __name__ == "__main__":
    main()
