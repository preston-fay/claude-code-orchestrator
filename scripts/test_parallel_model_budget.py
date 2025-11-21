#!/usr/bin/env python3
"""
Test script for parallel agent execution, model selection, and budget enforcement.

This script demonstrates:
1. Parallel agent execution within phases
2. Model selection based on user entitlements
3. Token budget enforcement with limits

Usage:
    python scripts/test_parallel_model_budget.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator_v2.core.engine import WorkflowEngine
from orchestrator_v2.core.model_selection import (
    select_model_for_agent,
    estimate_tokens_for_agent,
    DEFAULT_ROLE_MODELS,
)
from orchestrator_v2.core.state_models import PhaseType, PhaseDefinition
from orchestrator_v2.telemetry.budget_enforcer import BudgetEnforcer, BudgetExceededError
from orchestrator_v2.user.models import UserProfile, UserRole, TokenUsage
from orchestrator_v2.user.repository import FileSystemUserRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(label: str, value: str, success: bool = True):
    """Print a result line."""
    status = "✓" if success else "✗"
    print(f"  {status} {label}: {value}")


async def test_model_selection():
    """Test model selection based on user entitlements."""
    print_header("Test 1: Model Selection")

    # Create user with entitlements
    user = UserProfile(
        user_id="test-user-1",
        email="test@example.com",
        name="Test User",
        role=UserRole.DEVELOPER,
        llm_api_key="sk-test-123",
        llm_provider="anthropic",
        default_model="claude-sonnet-4-20250514",
        model_entitlements={
            "architect": ["claude-3-opus-20240229", "claude-sonnet-4-20250514"],
            "developer": ["claude-sonnet-4-20250514"],
            "qa": ["claude-3-5-haiku-20241022"],
        },
    )

    # Test model selection for different roles
    test_cases = [
        ("architect", "claude-3-opus-20240229"),  # First in entitlements
        ("developer", "claude-sonnet-4-20250514"),
        ("qa", "claude-3-5-haiku-20241022"),
        ("documentarian", "claude-sonnet-4-20250514"),  # Falls back to default
    ]

    all_passed = True
    for agent_role, expected_model in test_cases:
        config = select_model_for_agent(user, agent_role)
        passed = config.model == expected_model
        all_passed = all_passed and passed
        print_result(
            f"Model for {agent_role}",
            f"{config.model} (expected: {expected_model})",
            passed
        )

    # Test without user (global defaults)
    print("\n  Testing global defaults (no user):")
    for role, expected in DEFAULT_ROLE_MODELS.items():
        config = select_model_for_agent(None, role)
        passed = config.model == expected
        print_result(f"Default for {role}", config.model, passed)

    return all_passed


async def test_budget_enforcement():
    """Test token budget enforcement."""
    print_header("Test 2: Budget Enforcement")

    # Create user repository
    user_repo = FileSystemUserRepository()

    # Create user with budget limits
    user = UserProfile(
        user_id="budget-test-user",
        email="budget@example.com",
        name="Budget Test User",
        role=UserRole.DEVELOPER,
        llm_api_key="sk-test-456",
        token_limits={
            "project": 10000,  # 10k tokens per project
            "daily": 50000,    # 50k tokens per day
        },
        token_usage=TokenUsage(
            total_input_tokens=0,
            total_output_tokens=0,
            total_requests=0,
        ),
    )

    # Save user
    await user_repo.save(user)

    # Create budget enforcer
    enforcer = BudgetEnforcer(user_repo)

    # Test 1: Should pass - within budget
    try:
        await enforcer.check_and_reserve(user, "proj-123", 5000)
        print_result("Budget check (5000 tokens)", "PASSED", True)
    except BudgetExceededError as e:
        print_result("Budget check (5000 tokens)", f"FAILED: {e}", False)
        return False

    # Test 2: Should pass - near limit
    try:
        await enforcer.check_and_reserve(user, "proj-123", 4000)
        print_result("Budget check (4000 more tokens)", "PASSED", True)
    except BudgetExceededError as e:
        print_result("Budget check (4000 more tokens)", f"FAILED: {e}", False)
        return False

    # Test 3: Record some usage
    await enforcer.record_usage(
        user=user,
        project_id="proj-123",
        agent_role="developer",
        model="claude-sonnet-4-20250514",
        input_tokens=3000,
        output_tokens=2000,
    )
    print_result("Usage recorded", "5000 tokens", True)

    # Test 4: Create new user with very low budget
    low_budget_user = UserProfile(
        user_id="low-budget-user",
        email="low@example.com",
        name="Low Budget User",
        role=UserRole.DEVELOPER,
        token_limits={"project": 100},  # Very low limit
    )
    await user_repo.save(low_budget_user)

    # Test 5: Should fail - exceeds budget
    try:
        await enforcer.check_and_reserve(low_budget_user, "proj-456", 5000)
        print_result("Budget exceeded check", "SHOULD HAVE FAILED", False)
        return False
    except BudgetExceededError as e:
        print_result("Budget exceeded check", f"Correctly blocked: {e.limit_type}", True)

    # Get remaining budget
    remaining = await enforcer.get_remaining_budget(user, "proj-123")
    print_result("Remaining budget", str(remaining), True)

    return True


async def test_parallel_execution():
    """Test parallel agent execution."""
    print_header("Test 3: Parallel Agent Execution")

    # Create engine
    engine = WorkflowEngine()

    # Start a project
    state = await engine.start_project(
        project_name="Parallel Test Project",
        client="test-client",
    )
    print_result("Project created", state.project_id[:8] + "...", True)

    # Create user for the test
    user = UserProfile(
        user_id="parallel-test-user",
        email="parallel@example.com",
        name="Parallel Test User",
        role=UserRole.DEVELOPER,
        llm_api_key="sk-test-parallel",
        token_limits={"project": 100000},  # High limit for test
    )

    # Create a mock phase definition with multiple agents
    phase_def = PhaseDefinition(
        name=PhaseType.DEVELOPMENT,
        order=4,
        responsible_agents=["developer", "steward"],
    )

    print("\n  Executing agents in parallel...")

    # Time the execution
    start_time = datetime.utcnow()

    try:
        agent_states = await engine._run_agents_for_phase(phase_def, user)
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print_result("Parallel execution", f"Completed in {duration:.2f}s", True)

        # Print agent results
        total_tokens = 0
        for agent_id, agent_state in agent_states.items():
            tokens = agent_state.token_usage.total_tokens
            total_tokens += tokens
            print_result(
                f"  Agent: {agent_id}",
                f"model={agent_state.model_used}, tokens={tokens}",
                agent_state.status.value == "complete"
            )

        print_result("Total tokens", str(total_tokens), True)
        return True

    except Exception as e:
        print_result("Parallel execution", f"FAILED: {e}", False)
        return False


async def test_token_estimates():
    """Test token estimation for agents."""
    print_header("Test 4: Token Estimates")

    agents = ["architect", "developer", "data", "qa", "documentarian", "steward"]

    total_estimate = 0
    for agent in agents:
        estimate = estimate_tokens_for_agent(agent)
        total_estimate += estimate
        print_result(f"Estimate for {agent}", f"{estimate:,} tokens", True)

    print_result("Total phase estimate", f"{total_estimate:,} tokens", True)
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  Parallel Execution, Model Selection & Budget Enforcement")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Model Selection", await test_model_selection()))
    results.append(("Budget Enforcement", await test_budget_enforcement()))
    results.append(("Parallel Execution", await test_parallel_execution()))
    results.append(("Token Estimates", await test_token_estimates()))

    # Summary
    print_header("Test Summary")

    all_passed = True
    for name, passed in results:
        print_result(name, "PASSED" if passed else "FAILED", passed)
        all_passed = all_passed and passed

    print("\n" + "=" * 60)
    if all_passed:
        print("  All tests PASSED")
    else:
        print("  Some tests FAILED")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
