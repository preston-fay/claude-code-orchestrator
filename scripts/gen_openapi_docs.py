#!/usr/bin/env python3
"""
Generate OpenAPI documentation for Docusaurus from FastAPI server.

This script fetches the OpenAPI JSON from the running FastAPI server
and generates markdown documentation pages for Docusaurus.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
OUTPUT_DIR = Path(__file__).parent.parent / "site" / "docs" / "api"


def fetch_openapi_spec() -> Dict[str, Any]:
    """Fetch OpenAPI spec from the API server."""
    try:
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to API at {API_BASE_URL}")
        print("Make sure the server is running: orchestrator server start")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching OpenAPI spec: {e}")
        sys.exit(1)


def generate_endpoint_doc(path: str, method: str, operation: Dict[str, Any]) -> str:
    """Generate markdown documentation for a single endpoint."""
    summary = operation.get("summary", "")
    description = operation.get("description", "")
    tags = operation.get("tags", [])

    # Build markdown
    md = f"### `{method.upper()} {path}`\n\n"

    if summary:
        md += f"**{summary}**\n\n"

    if description:
        md += f"{description}\n\n"

    # Parameters
    if "parameters" in operation:
        md += "#### Parameters\n\n"
        for param in operation["parameters"]:
            name = param.get("name", "")
            location = param.get("in", "")
            required = param.get("required", False)
            param_type = param.get("schema", {}).get("type", "string")
            param_desc = param.get("description", "")

            req_badge = "**Required**" if required else "Optional"
            md += f"- **`{name}`** ({location}, {param_type}) - {req_badge}\n"
            if param_desc:
                md += f"  - {param_desc}\n"
        md += "\n"

    # Request Body
    if "requestBody" in operation:
        md += "#### Request Body\n\n"
        content = operation["requestBody"].get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            md += f"```json\n{json.dumps(schema, indent=2)}\n```\n\n"

    # Responses
    if "responses" in operation:
        md += "#### Responses\n\n"
        for status_code, response in operation["responses"].items():
            description = response.get("description", "")
            md += f"**{status_code}** - {description}\n\n"

            content = response.get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                if schema:
                    md += f"```json\n{json.dumps(schema, indent=2)}\n```\n\n"

    # Example
    md += "#### Example\n\n"
    md += f"```bash\ncurl -X {method.upper()} {API_BASE_URL}{path} \\\n"
    md += f"  -H \"Content-Type: application/json\" \\\n"
    md += f"  -H \"X-API-Key: your-api-key\"\n```\n\n"

    md += "---\n\n"
    return md


def generate_docs_by_tag(spec: Dict[str, Any]) -> None:
    """Generate documentation pages organized by tags."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Group endpoints by tag
    endpoints_by_tag: Dict[str, list] = {}

    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "patch", "delete"]:
                tags = operation.get("tags", ["Untagged"])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append((path, method, operation))

    # Generate a page for each tag
    for tag, endpoints in sorted(endpoints_by_tag.items()):
        filename = tag.lower().replace(" ", "-") + ".md"
        filepath = OUTPUT_DIR / filename

        # Create markdown content
        md = f"""---
sidebar_position: 100
title: {tag}
---

# {tag}

{spec.get('info', {}).get('description', '')}

"""

        for path, method, operation in sorted(endpoints):
            md += generate_endpoint_doc(path, method, operation)

        # Write file
        filepath.write_text(md)
        print(f"Generated: {filepath}")


def main():
    """Main entry point."""
    print("Generating OpenAPI documentation...")
    print(f"API URL: {API_BASE_URL}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Fetch spec
    spec = fetch_openapi_spec()
    print(f"Fetched OpenAPI spec version {spec.get('openapi', 'unknown')}")
    print(f"API title: {spec.get('info', {}).get('title', 'Unknown')}")
    print(f"API version: {spec.get('info', {}).get('version', 'Unknown')}")

    # Generate docs
    generate_docs_by_tag(spec)

    print("\nOpenAPI documentation generated successfully!")
    print(f"Total endpoints: {sum(len(p) for p in spec.get('paths', {}).values())}")


if __name__ == "__main__":
    main()
