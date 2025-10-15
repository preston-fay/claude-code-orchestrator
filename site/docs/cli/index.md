---
sidebar_position: 1
title: CLI Reference
---

# CLI Reference

Complete command-line interface documentation for the Kearney Data Platform orchestrator.

## Overview

The `orchestrator` CLI provides a powerful command-line interface for managing data, models, themes, and platform operations.

## Installation

```bash
pip install -e .
```

## Global Options

Available for all commands:

- `--help` - Show help message
- `--version` - Show version information
- `--verbose` / `-v` - Enable verbose output
- `--quiet` / `-q` - Suppress non-error output
- `--config` - Specify config file path

## Command Structure

```bash
orchestrator [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS]
```

## Quick Reference

### Server Commands

```bash
# Start the API server
orchestrator server start --port 8000

# Stop the server
orchestrator server stop

# Check server status
orchestrator server status
```

### Data Commands

```bash
# Query data
orchestrator data query "SELECT * FROM table"

# Load data from file
orchestrator data load data.csv --table my_table

# Export data
orchestrator data export my_table --format parquet
```

### Style Commands

```bash
# List available themes
orchestrator style list

# Create a new theme
orchestrator style create client-theme

# Apply a theme
orchestrator style apply client-theme

# Export theme for client delivery
orchestrator style export client-theme --format pdf
```

### Registry Commands

```bash
# Register a model
orchestrator registry register my-model --version 1.0.0

# List models
orchestrator registry list

# Get model details
orchestrator registry get my-model --version 1.0.0
```

### System Commands

```bash
# Check system health
orchestrator system status

# View system info
orchestrator system info

# Run diagnostics
orchestrator system check
```

### Security Commands

```bash
# Generate API key
orchestrator security generate-key --name my-key

# List API keys
orchestrator security list-keys

# Revoke API key
orchestrator security revoke-key key-id

# View audit logs
orchestrator security audit-log --since 24h
```

## Auto-Generated Documentation

Complete CLI documentation is automatically generated from the Typer CLI application.

See the sections below for detailed documentation of each command group.

## Configuration Files

The CLI looks for configuration in the following locations (in order):

1. `./orchestrator.yaml`
2. `~/.config/orchestrator/config.yaml`
3. `/etc/orchestrator/config.yaml`

Example configuration:

```yaml
api:
  base_url: http://localhost:8000
  api_key: ${API_KEY}

database:
  path: ./data/platform.duckdb

logging:
  level: INFO
  format: json

themes:
  default: kearney-light
  output_dir: ./output/themes
```

## Environment Variables

- `ORCHESTRATOR_API_KEY` - API key for authentication
- `ORCHESTRATOR_BASE_URL` - API base URL
- `ORCHESTRATOR_CONFIG` - Config file path
- `ORCHESTRATOR_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - Authentication error
- `4` - Not found error
- `5` - Validation error

## Examples

### Complete Workflow Example

```bash
# 1. Start the server
orchestrator server start --port 8000

# 2. Load data
orchestrator data load sales_data.csv --table sales

# 3. Query data
orchestrator data query "SELECT region, SUM(revenue) FROM sales GROUP BY region"

# 4. Create a client theme
orchestrator style create acme-corp

# 5. Generate visualizations
orchestrator viz create sales --theme acme-corp

# 6. Export for client delivery
orchestrator style export acme-corp --format pdf --output acme-theme.pdf
```

### Batch Operations

```bash
# Process multiple files
for file in data/*.csv; do
  orchestrator data load "$file" --table "$(basename $file .csv)"
done

# Generate themes for multiple clients
cat clients.txt | while read client; do
  orchestrator style create "$client-theme"
done
```

## Getting Help

For detailed help on any command:

```bash
orchestrator COMMAND --help
```

For specific subcommand help:

```bash
orchestrator COMMAND SUBCOMMAND --help
```
