#!/usr/bin/env bash
# Sandbox self-test: Verify that network blocking works

set -euo pipefail

echo "🧪 Running sandbox self-test..."
echo ""

# Test 1: Verify that import guard blocks dangerous imports
echo "Test 1: Import guard blocks dangerous imports"
python3 -c "
import sys
sys.path.insert(0, 'src')
from orchestrator.executors.sandbox import static_import_guard

code = '''
import os
import socket
'''

is_safe, violations = static_import_guard(code)
if is_safe:
    print('  ✗ FAIL: Import guard did not block dangerous imports')
    sys.exit(1)
else:
    print('  ✓ PASS: Import guard blocked dangerous imports')
"

# Test 2: Verify that safety validation catches eval/exec
echo "Test 2: Safety validation catches eval/exec"
python3 -c "
import sys
sys.path.insert(0, 'src')
from orchestrator.executors.sandbox import validate_code_safety

code = '''
result = eval(\"1 + 1\")
'''

is_safe, violations = validate_code_safety(code)
if is_safe:
    print('  ✗ FAIL: Safety validation did not catch eval')
    sys.exit(1)
else:
    print('  ✓ PASS: Safety validation caught eval')
"

# Test 3: Verify that network patching code exists
echo "Test 3: Network patching code generation"
python3 -c "
import sys
sys.path.insert(0, 'src')
from orchestrator.executors.sandbox import patch_socket_if_no_network

patch = patch_socket_if_no_network()
if not patch or 'socket' not in patch:
    print('  ✗ FAIL: Network patching code not generated')
    sys.exit(1)
else:
    print('  ✓ PASS: Network patching code generated')
"

# Test 4: Verify that allowlist works correctly
echo "Test 4: Module allowlist validation"
python3 -c "
import sys
sys.path.insert(0, 'src')
from orchestrator.executors.sandbox import _is_module_allowed

# Safe modules
if not _is_module_allowed('json'):
    print('  ✗ FAIL: json should be allowed')
    sys.exit(1)
if not _is_module_allowed('orchestrator.mcp.data'):
    print('  ✗ FAIL: orchestrator.mcp.data should be allowed')
    sys.exit(1)

# Dangerous modules
if _is_module_allowed('os'):
    print('  ✗ FAIL: os should be blocked')
    sys.exit(1)
if _is_module_allowed('subprocess'):
    print('  ✗ FAIL: subprocess should be blocked')
    sys.exit(1)

print('  ✓ PASS: Module allowlist working correctly')
"

echo ""
echo "✅ All sandbox self-tests passed!"
exit 0
