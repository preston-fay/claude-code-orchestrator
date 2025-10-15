#!/usr/bin/env python3
"""
Theme Merge Script

Merges base Kearney design tokens with client-specific theme overrides.
Validates against JSON schema and generates CSS/TypeScript token files.

Usage:
    python scripts/merge_theme.py --client <slug>
    python scripts/merge_theme.py --client acme-corp --output design_system/.generated
"""

import argparse
import json
import jsonschema
from pathlib import Path
from typing import Dict, Any
import sys


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary with overrides taking precedence
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def validate_theme(theme: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate theme against JSON schema.

    Args:
        theme: Theme JSON to validate
        schema: JSON schema

    Returns:
        Tuple of (valid, errors)
    """
    try:
        jsonschema.validate(instance=theme, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        return False, [e.message]
    except jsonschema.SchemaError as e:
        return False, [f"Schema error: {str(e)}"]


def generate_css_tokens(tokens: Dict[str, Any], output_path: Path):
    """
    Generate CSS custom properties from tokens.

    Args:
        tokens: Token dictionary
        output_path: Path to write CSS file
    """
    lines = [
        "/**",
        " * Kearney Design Tokens - Auto-generated",
        " * DO NOT EDIT MANUALLY - Generated from base tokens + client overrides",
        " */",
        "",
        ":root {",
    ]

    # Extract colors for light mode
    if "colors" in tokens and "light" in tokens["colors"]:
        lines.append("  /* Light Mode Colors */")
        for key, value in tokens["colors"]["light"].items():
            css_key = key.replace("_", "-")
            lines.append(f"  --{css_key}: {value};")
        lines.append("")

    # Extract typography
    if "typography" in tokens:
        lines.append("  /* Typography */")
        for key, value in tokens["typography"].items():
            css_key = key.replace("_", "-")
            # Convert camelCase to kebab-case
            css_key = "".join([f"-{c.lower()}" if c.isupper() else c for c in css_key]).lstrip("-")
            lines.append(f"  --{css_key}: {value};")
        lines.append("")

    # Extract spacing
    if "spacing" in tokens:
        lines.append("  /* Spacing */")
        for key, value in tokens["spacing"].items():
            css_key = key.replace("_", "-")
            lines.append(f"  --spacing-{css_key}: {value};")
        lines.append("")

    lines.append("}")
    lines.append("")

    # Dark mode
    if "colors" in tokens and "dark" in tokens["colors"]:
        lines.append("[data-theme='dark'] {")
        lines.append("  /* Dark Mode Colors */")
        for key, value in tokens["colors"]["dark"].items():
            css_key = key.replace("_", "-")
            lines.append(f"  --{css_key}: {value};")
        lines.append("}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def generate_typescript_tokens(tokens: Dict[str, Any], output_path: Path):
    """
    Generate TypeScript token exports.

    Args:
        tokens: Token dictionary
        output_path: Path to write TypeScript file
    """
    lines = [
        "/**",
        " * Kearney Design Tokens - Auto-generated",
        " * DO NOT EDIT MANUALLY - Generated from base tokens + client overrides",
        " */",
        "",
        "export const tokens = " + json.dumps(tokens, indent=2) + " as const;",
        "",
        "export type Theme = 'light' | 'dark';",
        "",
        "export function getThemeColors(theme: Theme) {",
        "  return tokens.colors[theme];",
        "}",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Merge base tokens with client theme overrides")
    parser.add_argument("--client", required=True, help="Client slug (e.g., acme-corp)")
    parser.add_argument(
        "--output",
        default="design_system/.generated",
        help="Output directory for generated files",
    )
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't generate")
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    base_tokens_path = project_root / "design_system" / "tokens.json"
    client_theme_path = project_root / "clients" / args.client / "theme.json"
    schema_path = project_root / "clients" / ".schema" / "theme.schema.json"
    output_dir = project_root / args.output

    # Load files
    print(f"Loading base tokens from {base_tokens_path}")
    if not base_tokens_path.exists():
        print(f"Error: Base tokens not found at {base_tokens_path}", file=sys.stderr)
        sys.exit(1)
    base_tokens = load_json(base_tokens_path)

    print(f"Loading client theme from {client_theme_path}")
    if not client_theme_path.exists():
        print(f"Error: Client theme not found at {client_theme_path}", file=sys.stderr)
        sys.exit(1)
    client_theme = load_json(client_theme_path)

    # Validate theme
    print(f"Loading schema from {schema_path}")
    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}", file=sys.stderr)
        sys.exit(1)
    schema = load_json(schema_path)

    print("Validating client theme...")
    valid, errors = validate_theme(client_theme, schema)
    if not valid:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    print("✓ Theme validation passed")

    if args.validate_only:
        print("Validation complete (--validate-only specified)")
        return

    # Merge tokens
    print("Merging base tokens with client overrides...")
    merged_tokens = deep_merge(base_tokens, client_theme)

    # Add client metadata
    merged_tokens["_client"] = {
        "slug": args.client,
        "name": client_theme.get("client", {}).get("name", args.client),
        "generated_from": ["design_system/tokens.json", f"clients/{args.client}/theme.json"],
    }

    # Generate output files
    print(f"Generating CSS tokens to {output_dir / args.client}.css")
    generate_css_tokens(merged_tokens, output_dir / f"{args.client}.css")

    print(f"Generating TypeScript tokens to {output_dir / args.client}.ts")
    generate_typescript_tokens(merged_tokens, output_dir / f"{args.client}.ts")

    print(f"Generating merged JSON to {output_dir / args.client}.json")
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / f"{args.client}.json", "w") as f:
        json.dump(merged_tokens, f, indent=2)

    print(f"✓ Successfully generated tokens for client: {args.client}")
    print(f"  - CSS:        {output_dir / args.client}.css")
    print(f"  - TypeScript: {output_dir / args.client}.ts")
    print(f"  - JSON:       {output_dir / args.client}.json")


if __name__ == "__main__":
    main()
