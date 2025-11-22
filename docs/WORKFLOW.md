# Development Workflow

This document outlines the development workflow for the Claude Code Orchestrator project, with **Claude Code Worktree (CCW)** as the primary development interface.

## Overview

The repository at `https://github.com/preston-fay/claude-code-orchestrator.git` is the **source of truth**. All development should flow through Claude Code to maintain consistency and traceability.

## Workflow Steps

### 1. Use CCW to Code

- Open Claude Code and connect to the GitHub repository
- Create feature branches using CCW commands
- Write and edit code through the CCW interface
- CCW handles formatting, linting, and best practices automatically

### 2. Push to GitHub

- Commit changes through CCW with descriptive commit messages
- Push branches to origin using CCW
- All commits are tagged with Claude Code attribution

### 3. Develop and Review in GitHub UI

- Create pull requests from feature branches to `main`
- Review code changes in GitHub's PR interface
- Use GitHub Actions for CI/CD (if configured)
- Approve and merge PRs through GitHub

### 4. Pull Locally for Testing

- Pull the latest `main` branch to your local machine
- Run tests and start local development servers
- Verify changes work as expected
- **Do not make manual edits locally**—use CCW for all code changes

## Important Guidelines

### Avoid Local Manual Edits

To maintain sync and traceability:

- **Do NOT** edit files directly in your local editor
- **Do NOT** commit changes from local without going through CCW
- **ALWAYS** use CCW as the primary code editing interface

### Branch Strategy

- `main` - Production-ready code
- Feature branches - Created via CCW for each task
- Use descriptive branch names: `feat/feature-name`, `fix/bug-name`, `docs/update-name`

### Commit Messages

Follow conventional commits format:

```
type(scope): description

- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance
```

All commits include Claude Code attribution footer.

## Quick Reference

| Task | Method |
|------|--------|
| Write new code | CCW |
| Edit existing code | CCW |
| Create branches | CCW |
| Commit changes | CCW |
| Push to GitHub | CCW |
| Create PRs | CCW or GitHub UI |
| Review PRs | GitHub UI |
| Merge PRs | GitHub UI |
| Run tests | Local terminal |
| Start dev server | Local terminal |

## RSC Architecture: Generic Orchestrator

### RSC is Template-Agnostic

Ready-Set-Code (RSC) is designed as a **generic project orchestrator** that can manage any type of project:

- **App builds** (React + FastAPI applications)
- **Analytics projects** (forecasting, optimization)
- **Data pipelines** (ETL, ML training)
- **Custom domains** (any structured workflow)

RSC provides:
- Project lifecycle management (Ready / Set / Go phases)
- Workspace and repository management
- Agent and skill orchestration
- Budget, model, and governance controls
- Feature planning and app building

### Territory Optimizer is an Example Consumer

The **Territory Optimizer** is an example external application that demonstrates how to use RSC APIs. It is NOT a core part of RSC:

- Lives in a **separate repository** (`territory-optimizer-ui`)
- Calls RSC's `/territory/*` demo endpoints
- Has its own React UI for map visualization
- Uses RSC-managed skills for scoring and clustering

The `/territory/*` endpoints in `orchestrator_v2/api/server.py` are **demo APIs** that show how external apps can call RSC-managed skills. RSC itself does not depend on or assume any specific domain.

### Creating New Project Types

To add support for a new domain (e.g., "pricing optimization"):

1. **Create skills** under `orchestrator_v2/capabilities/skills/your_domain/`
2. **Add a template** in `orchestrator_v2/config/templates.py`
3. **Optionally add demo endpoints** for external consumers
4. **Build your UI** that calls the RSC API

The core RSC engine, RSG workflow, and UI all remain unchanged—they work with any project type automatically.

## Repository Information

- **GitHub URL**: https://github.com/preston-fay/claude-code-orchestrator.git
- **Default Branch**: `main`
- **Primary Interface**: Claude Code Worktree (CCW)

---

*This workflow ensures all code changes are tracked, attributed, and maintain high quality standards through the Claude Code development process.*
