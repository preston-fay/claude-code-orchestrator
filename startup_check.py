#!/usr/bin/env python3
"""Startup diagnostic script to identify import issues."""

import sys
import traceback

def check_import(module_name: str) -> bool:
    """Try to import a module and report status."""
    try:
        __import__(module_name)
        print(f"✓ {module_name}")
        return True
    except Exception as e:
        print(f"✗ {module_name}: {e}")
        return False

print("=" * 60)
print("ORCHESTRATOR V2 STARTUP DIAGNOSTIC")
print("=" * 60)
print(f"Python version: {sys.version}")
print()

print("Checking core dependencies...")
core_deps = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic_settings",
    "httpx",
    "anthropic",
    "boto3",
    "pandas",
    "numpy",
    "sklearn",
    "yaml",
    "rich",
    "typer",
    "click",
]

all_ok = True
for dep in core_deps:
    if not check_import(dep):
        all_ok = False

print()
print("Checking orchestrator_v2 modules...")
orchestrator_modules = [
    "orchestrator_v2",
    "orchestrator_v2.engine",
    "orchestrator_v2.engine.engine",
    "orchestrator_v2.engine.state_models",
    "orchestrator_v2.agents",
    "orchestrator_v2.llm",
    "orchestrator_v2.api",
    "orchestrator_v2.api.server",
    "orchestrator_v2.api.dto",
    "orchestrator_v2.auth",
    "orchestrator_v2.auth.dependencies",
    "orchestrator_v2.user",
    "orchestrator_v2.user.models",
    "orchestrator_v2.rsg",
    "orchestrator_v2.rsg.service",
    "orchestrator_v2.capabilities",
    "orchestrator_v2.capabilities.skills",
    "orchestrator_v2.capabilities.skills.territory_poc",
]

for mod in orchestrator_modules:
    if not check_import(mod):
        all_ok = False

print()
if all_ok:
    print("✓ All imports successful!")
    print()
    print("Attempting to create FastAPI app...")
    try:
        from orchestrator_v2.api.server import app
        print(f"✓ FastAPI app created: {app.title}")
    except Exception as e:
        print(f"✗ Failed to create app: {e}")
        traceback.print_exc()
else:
    print("✗ Some imports failed - see above")
    sys.exit(1)

print()
print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
