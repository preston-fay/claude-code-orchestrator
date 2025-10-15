---
sidebar_position: 1
title: API Reference
---

# API Reference

Complete REST API documentation for the Kearney Data Platform.

## Overview

The Kearney Data Platform provides a RESTful API built with FastAPI. The API includes automatic OpenAPI (Swagger) documentation, request validation, and comprehensive error handling.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com/api
```

## Authentication

All API endpoints require authentication using API keys or OAuth2 tokens.

```bash
curl -H "X-API-Key: your-api-key" https://api.example.com/endpoint
```

See the [Security documentation](/security) for details on obtaining and using API keys.

## Auto-Generated Documentation

The API documentation is automatically generated from the FastAPI OpenAPI specification.

View the interactive Swagger UI at: `{base_url}/docs`
View the ReDoc documentation at: `{base_url}/redoc`
Download the OpenAPI spec at: `{base_url}/openapi.json`

## Quick Examples

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Query Data

```bash
curl -X POST http://localhost:8000/data/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"sql": "SELECT * FROM table LIMIT 10"}'
```

### Upload Data

```bash
curl -X POST http://localhost:8000/data/upload \
  -H "X-API-Key: your-key" \
  -F "file=@data.csv"
```

## API Sections

The full API documentation is organized into the following sections:

- **Data Operations** - Query, upload, and manage datasets
- **Model Registry** - Register and retrieve models
- **Themes** - Manage client themes and styling
- **Security** - API key management and authentication
- **System** - Health checks and system information

For complete endpoint documentation, see the auto-generated pages below.
