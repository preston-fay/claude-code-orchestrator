#!/usr/bin/env bash
# Steward Check: Ensure no backup YAML files are tracked in git
# Part of Phase 1.1 - Repository Hygiene
set -euo pipefail

if git ls-files --error-unmatch 'backups/*.yaml' >/dev/null 2>&1; then
  echo "ERROR: backups/*.yaml is tracked. Move to ~/.orchestrator/backups/ and git rm it." >&2
  echo "" >&2
  echo "To fix:" >&2
  echo "  cp backups/*.yaml ~/.orchestrator/backups/" >&2
  echo "  git rm --cached backups/*.yaml" >&2
  echo "  git commit -m 'chore: untrack backup YAML files'" >&2
  exit 1
fi

echo "✓ OK: no tracked backup YAMLs."
exit 0
