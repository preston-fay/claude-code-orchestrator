# Backups Directory

This directory previously contained configuration backups that are now relocated to maintain repository hygiene.

## Relocation

All backup files have been moved to: `~/.orchestrator/backups/`

This keeps the repository clean while preserving important configuration history locally.

## Restore Instructions

If you need to restore old backups:

```bash
# List available backups
ls -lh ~/.orchestrator/backups/

# Copy a specific backup back
cp ~/.orchestrator/backups/config_20251014_211132.yaml config/

# Or restore all backups to this directory
cp ~/.orchestrator/backups/*.yaml backups/
```

## Why This Change?

Per ADR-000-repo-hygiene:
- Backup files are ephemeral artifacts, not source code
- They should not be version controlled
- Local backup storage is more appropriate
- Keeps git history clean and repository size manageable

## Current Backups

The following files were relocated on 2025-11-14:

- config_*.yaml (7 files)
- hygiene_*.yaml (1 file)

Non-YAML backup files (Python source backups) remain in this directory for now and will be evaluated separately.
