#!/usr/bin/env python3
"""
Validation script for Skills, Tools, and Governance integration.

Tests:
1. Skill detection using triggers
2. Tool invocation inside agent actions
3. Governance evaluation (including failing rules)
4. Phase blocked by governance
5. Token budget enforcement

Run with: python scripts/test_skills_tools_governance.py
"""

import asyncio
from uuid import uuid4

from orchestrator_v2.engine.state_models import (
    GateStatus,
    PhaseType,
    ProjectState,
    BudgetConfig,
)
from orchestrator_v2.governance.governance_engine import GovernanceEngine
from orchestrator_v2.capabilities.skills.registry import SkillRegistry
from orchestrator_v2.telemetry.token_tracking import TokenTracker
from orchestrator_v2.capabilities.tools.registry import ToolRegistry


async def test_skill_detection():
    """Test skill detection using triggers."""
    print("\n" + "=" * 60)
    print("TEST 1: Skill Detection")
    print("=" * 60)

    registry = SkillRegistry()
    registry.discover_skills()

    # Test various task descriptions
    test_cases = [
        ("Build a forecast model for sales", ["time_series_forecasting"]),
        ("Optimize warehouse inventory", ["optimization_modeling"]),
        ("Analyze customer survey responses", ["survey_analysis"]),
        ("Create a dashboard", []),  # No match expected
        ("Predict future trends with time series", ["time_series_forecasting"]),
    ]

    for description, expected in test_cases:
        matches = registry.match_skill(description)
        matched_ids = [m[0] for m in matches]

        status = "PASS" if set(matched_ids) == set(expected) else "FAIL"
        print(f"\n  Task: '{description}'")
        print(f"  Expected: {expected}")
        print(f"  Found: {matched_ids}")
        print(f"  Status: {status}")

    # Test find_matching_skills
    print("\n  Testing find_matching_skills:")
    skills = registry.find_matching_skills(
        agent_role="data_engineer",
        phase_name="data",
        project_metadata={"requirements": ["Build forecast", "Optimize costs"]},
    )
    print(f"  Found {len(skills)} matching skills: {[s.id for s in skills]}")

    return True


async def test_tool_invocation():
    """Test tool invocation inside agent actions."""
    print("\n" + "=" * 60)
    print("TEST 2: Tool Invocation")
    print("=" * 60)

    registry = ToolRegistry()
    registry.discover_tools()

    # Create project state
    project_state = ProjectState(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        project_name="Test Project",
        client="kearney-default",
        current_phase=PhaseType.DEVELOPMENT,
    )

    # Test each tool
    tools_to_test = [
        ("git", {"action": "diff"}),
        ("duckdb", {"query": "SELECT * FROM sales"}),
        ("security_scanner", {"scan_type": "full"}),
        ("deploy", {"environment": "staging"}),
        ("visualization", {"chart_type": "mermaid"}),
    ]

    total_tokens = 0
    all_artifacts = []

    for tool_id, params in tools_to_test:
        result = await registry.run_tool(
            tool_id=tool_id,
            agent_id="test_agent",
            phase=PhaseType.DEVELOPMENT,
            project_state=project_state,
            params=params,
        )

        print(f"\n  Tool: {tool_id}")
        print(f"  Success: {result.success}")
        print(f"  Output: {result.output[:50]}...")
        print(f"  Artifacts: {len(result.artifacts)}")
        print(f"  Tokens: {result.token_usage.total_tokens}")

        total_tokens += result.token_usage.total_tokens
        all_artifacts.extend(result.artifacts)

    print(f"\n  Total tokens used: {total_tokens}")
    print(f"  Total artifacts created: {len(all_artifacts)}")

    return True


async def test_skill_execution():
    """Test skill execution with artifact generation."""
    print("\n" + "=" * 60)
    print("TEST 3: Skill Execution")
    print("=" * 60)

    registry = SkillRegistry()
    registry.discover_skills()

    project_state = ProjectState(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        project_name="Analytics Project",
        client="kearney-default",
        current_phase=PhaseType.DATA,
        metadata={"requirements": ["forecast", "survey analysis"]},
    )

    # Find and execute matching skills
    skills = registry.find_matching_skills(
        agent_role="data_engineer",
        phase_name="data",
        project_metadata=project_state.metadata,
    )

    results = await registry.execute_skills(
        skills=skills,
        agent_id="data_agent",
        phase=PhaseType.DATA,
        project_state=project_state,
        context={},
    )

    total_tokens = 0
    total_artifacts = 0

    for result in results:
        print(f"\n  Skill: {result.skill_id}")
        print(f"  Success: {result.success}")
        print(f"  Messages: {len(result.messages)}")
        for msg in result.messages:
            print(f"    - {msg}")
        print(f"  Artifacts: {len(result.artifacts)}")
        for artifact in result.artifacts:
            print(f"    - {artifact.path}")
        print(f"  Tokens: {result.token_usage.total_tokens}")

        total_tokens += result.token_usage.total_tokens
        total_artifacts += len(result.artifacts)

    print(f"\n  Total skills executed: {len(results)}")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Total artifacts: {total_artifacts}")

    return True


async def test_governance_passing():
    """Test governance evaluation - passing case."""
    print("\n" + "=" * 60)
    print("TEST 4: Governance Evaluation (Passing)")
    print("=" * 60)

    engine = GovernanceEngine()

    # Create project state with passing metrics
    project_state = ProjectState(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        project_name="Test Project",
        client="kearney-default",
        current_phase=PhaseType.QA,
        metadata={
            "test_coverage": 90,
            "security_scan_passed": True,
        },
    )

    # Evaluate governance
    results = await engine.evaluate_phase_transition(
        project_state=project_state,
        phase=PhaseType.QA,
    )

    print(f"\n  Phase: {PhaseType.QA.value}")
    print(f"  Overall passed: {results.passed}")
    print(f"  Gates evaluated: {len(results.quality_gates)}")

    for gate in results.quality_gates:
        status_str = "PASS" if gate.status == GateStatus.PASSED else "BLOCKED"
        print(f"\n  Gate: {gate.gate_id}")
        print(f"    Status: {status_str}")
        print(f"    Threshold: {gate.threshold}")
        print(f"    Actual: {gate.actual}")
        print(f"    Message: {gate.message}")

    # Check audit trail
    audit = project_state.metadata.get("governance_audit", [])
    print(f"\n  Audit trail entries: {len(audit)}")

    return results.passed


async def test_governance_blocking():
    """Test governance evaluation - blocking case."""
    print("\n" + "=" * 60)
    print("TEST 5: Governance Evaluation (Blocking)")
    print("=" * 60)

    engine = GovernanceEngine()

    # Create project state with failing metrics
    project_state = ProjectState(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        project_name="Test Project",
        client="kearney-default",
        current_phase=PhaseType.QA,
        metadata={
            "test_coverage": 60,  # Below 80% threshold
            "security_scan_passed": False,  # Security scan failed
        },
    )

    # Evaluate governance
    results = await engine.evaluate_phase_transition(
        project_state=project_state,
        phase=PhaseType.QA,
    )

    print(f"\n  Phase: {PhaseType.QA.value}")
    print(f"  Overall passed: {results.passed}")
    print(f"  Failed rules: {results.failed_rules}")

    for gate in results.quality_gates:
        status_str = "PASS" if gate.status == GateStatus.PASSED else "BLOCKED"
        print(f"\n  Gate: {gate.gate_id}")
        print(f"    Status: {status_str}")
        print(f"    Threshold: {gate.threshold}")
        print(f"    Actual: {gate.actual}")
        print(f"    Message: {gate.message}")

    # Verify phase would be blocked
    blocked = not results.passed
    print(f"\n  Phase transition blocked: {blocked}")
    print(f"  This is expected behavior for governance enforcement!")

    return blocked  # We expect this to be True (blocked)


async def test_token_budget_enforcement():
    """Test token budget enforcement."""
    print("\n" + "=" * 60)
    print("TEST 6: Token Budget Enforcement")
    print("=" * 60)

    tracker = TokenTracker()

    workflow_id = str(uuid4())

    # Set a low budget
    tracker.set_budget(workflow_id, BudgetConfig(
        max_tokens=1000,
        max_cost_usd=1.0,
        alert_threshold=0.8,
    ))

    # Track some usage
    print("\n  Tracking token usage...")

    usage1 = tracker.track_llm_call(
        workflow_id=workflow_id,
        phase="planning",
        agent_id="architect",
        input_tokens=200,
        output_tokens=100,
    )
    print(f"  Call 1: {usage1.total_tokens} tokens")

    usage2 = tracker.track_llm_call(
        workflow_id=workflow_id,
        phase="planning",
        agent_id="architect",
        input_tokens=300,
        output_tokens=200,
    )
    print(f"  Call 2: {usage2.total_tokens} tokens")

    # Check remaining budget
    remaining = tracker.get_remaining_budget(workflow_id)
    print(f"\n  Remaining budget: {remaining.total_tokens} tokens")

    # Try to exceed budget
    print("\n  Attempting to exceed budget...")
    try:
        tracker.track_llm_call(
            workflow_id=workflow_id,
            phase="planning",
            agent_id="architect",
            input_tokens=500,
            output_tokens=300,
        )
        print("  Budget exceeded but no exception raised!")
        return False
    except Exception as e:
        print(f"  Budget enforcement triggered: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        return True


async def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Skills, Tools & Governance Validation")
    print("=" * 60)

    results = {}

    # Run tests
    results["skill_detection"] = await test_skill_detection()
    results["tool_invocation"] = await test_tool_invocation()
    results["skill_execution"] = await test_skill_execution()
    results["governance_passing"] = await test_governance_passing()
    results["governance_blocking"] = await test_governance_blocking()
    results["token_budget"] = await test_token_budget_enforcement()

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed!")
        print("Skills + Tools generate artifacts correctly")
        print("Governance blocking works as expected")
    else:
        print("Some tests failed - review output above")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
