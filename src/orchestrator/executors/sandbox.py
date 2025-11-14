"""Sandbox utilities for safe code execution.

This module provides helpers for:
- Resource limits (CPU, memory, timeout)
- Network blocking
- Import whitelist enforcement
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Optional, Set


# Allowed standard library modules for data processing
SAFE_STDLIB_MODULES = {
    "json",
    "csv",
    "pathlib",
    "typing",
    "math",
    "statistics",
    "datetime",
    "collections",
    "itertools",
    "functools",
    "re",
    "pickle",
    "io",
}

# Allowed third-party modules
SAFE_THIRD_PARTY_MODULES = {
    "pandas",
    "numpy",
    "matplotlib",
    "matplotlib.pyplot",
    "sklearn",
    "scipy",
}

# Disallowed modules that can cause security issues
DISALLOWED_MODULES = {
    "os",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "ftplib",
    "telnetlib",
    "eval",
    "exec",
    "compile",
    "__import__",
    "importlib",
    "sys",  # Some sys functions are dangerous
}


def static_import_guard(code: str) -> tuple[bool, List[str]]:
    """Check if code contains only allowed imports.

    Args:
        code: Python code to analyze

    Returns:
        Tuple of (is_safe: bool, violations: List[str])
        is_safe is True if all imports are allowed, False otherwise
        violations is a list of disallowed import statements found

    Example:
        >>> code = "import pandas\\nimport os"
        >>> is_safe, violations = static_import_guard(code)
        >>> print(is_safe)
        False
        >>> print(violations)
        ['import os']
    """
    violations = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax error: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                if not _is_module_allowed(module_name):
                    violations.append(f"import {module_name}")

        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            if not _is_module_allowed(module_name):
                violations.append(f"from {module_name} import ...")

    is_safe = len(violations) == 0
    return is_safe, violations


def _is_module_allowed(module_name: str) -> bool:
    """Check if a module is allowed to be imported.

    Args:
        module_name: Full module name (e.g., "orchestrator.mcp.data")

    Returns:
        True if module is allowed, False otherwise
    """
    # Check disallowed first
    for disallowed in DISALLOWED_MODULES:
        if module_name == disallowed or module_name.startswith(f"{disallowed}."):
            return False

    # Allow orchestrator.mcp.* modules
    if module_name.startswith("orchestrator.mcp."):
        return True

    # Check safe stdlib
    base_module = module_name.split(".")[0]
    if base_module in SAFE_STDLIB_MODULES:
        return True

    # Check safe third-party
    if module_name in SAFE_THIRD_PARTY_MODULES:
        return True
    if base_module in {m.split(".")[0] for m in SAFE_THIRD_PARTY_MODULES}:
        return True

    return False


def set_rlimits_if_available(cpu_seconds: int = 120, mem_bytes: int = 1024 * 1024 * 1024):
    """Set resource limits using POSIX rlimit (if available).

    Args:
        cpu_seconds: Maximum CPU time in seconds (default: 120)
        mem_bytes: Maximum memory in bytes (default: 1GB)

    Note:
        This function only works on POSIX systems. On Windows or if
        the resource module is not available, it logs a warning and continues.
    """
    try:
        import resource

        # Set CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))

        # Set memory limit (if supported)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except (ValueError, OSError):
            # Some systems don't support RLIMIT_AS
            pass

    except ImportError:
        # resource module not available (Windows)
        print(
            "Warning: resource module not available. "
            "CPU and memory limits cannot be enforced.",
            file=sys.stderr,
        )
    except Exception as e:
        print(f"Warning: Failed to set resource limits: {e}", file=sys.stderr)


def patch_socket_if_no_network() -> Optional[str]:
    """Monkeypatch socket module to block network access.

    Returns:
        Python code snippet to inject at the start of the sandbox script,
        or None if patching is not needed.

    Example:
        >>> patch_code = patch_socket_if_no_network()
        >>> if patch_code:
        ...     full_code = patch_code + "\\n\\n" + user_code
    """
    patch_code = '''
# Network blocking patch
import socket as _socket
_original_socket = _socket.socket

def _blocked_socket(*args, **kwargs):
    raise RuntimeError(
        "Network access is disabled in sandbox mode. "
        "If you need to load data, use local files or environment-provided connection strings."
    )

_socket.socket = _blocked_socket
'''
    return patch_code


def validate_code_safety(code: str) -> tuple[bool, List[str]]:
    """Comprehensive safety validation for code.

    Checks for:
    - Disallowed imports
    - Dangerous function calls (eval, exec, compile, __import__)
    - System command execution patterns

    Args:
        code: Python code to validate

    Returns:
        Tuple of (is_safe: bool, violations: List[str])
    """
    violations = []

    # Check imports
    is_safe_imports, import_violations = static_import_guard(code)
    violations.extend(import_violations)

    # Check for eval/exec/compile
    dangerous_calls = ["eval(", "exec(", "compile(", "__import__("]
    for call in dangerous_calls:
        if call in code:
            violations.append(f"Dangerous function call: {call}")

    # Check for os.system, subprocess patterns
    dangerous_patterns = [
        r'os\.system\s*\(',
        r'subprocess\.',
        r'open\s*\(\s*["\'][/\\]',  # Absolute path opens can be risky
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, code):
            violations.append(f"Dangerous pattern: {pattern}")

    is_safe = len(violations) == 0
    return is_safe, violations
