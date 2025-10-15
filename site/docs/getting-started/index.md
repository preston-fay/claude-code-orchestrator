---
sidebar_position: 1
title: Getting Started
---

# Getting Started with Kearney Data Platform

This guide will help you set up and start using the Kearney Data Platform in minutes.

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- AWS account (for deployment)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/claude-code-orchestrator.git
cd claude-code-orchestrator
```

### 2. Install Python Dependencies

```bash
pip install -r requirements-dataplatform.txt
```

### 3. Install CLI Tool

```bash
pip install -e .
```

### 4. Verify Installation

```bash
orchestrator --version
```

## Quick Start

### Start the API Server

```bash
orchestrator server start --port 8000
```

The server will start at [http://localhost:8000](http://localhost:8000).

View the interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### Start the Frontend

```bash
cd apps/web
npm install
npm run dev
```

The frontend will start at [http://localhost:5173](http://localhost:5173).

### Run the CLI

```bash
# View available commands
orchestrator --help

# Check system status
orchestrator system status

# Query data
orchestrator data query "SELECT * FROM my_table LIMIT 10"

# Create a theme
orchestrator style create my-client-theme
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_BASE_URL=http://localhost:8000
API_KEY=your-api-key-here

# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Database Setup

The platform uses DuckDB for data storage. No additional database setup is required.

```bash
# Initialize the database
orchestrator db init

# Run migrations (if any)
orchestrator db migrate
```

## Next Steps

- [API Reference](/api) - Explore the REST API
- [CLI Reference](/cli) - Learn all CLI commands
- [Design System](/design-system) - Understand the design tokens
- [Operations](/ops) - Deploy to production
- [Security](/security) - Configure authentication

## Common Issues

### Port Already in Use

If port 8000 or 5173 is already in use:

```bash
# Use a different port
orchestrator server start --port 8001

# Or kill the existing process
lsof -ti:8000 | xargs kill -9
```

### Module Not Found

Ensure you've installed the package in editable mode:

```bash
pip install -e .
```

### Permission Errors

On Linux/macOS, you may need to use:

```bash
pip install --user -e .
```
