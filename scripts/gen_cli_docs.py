#!/usr/bin/env python3
"""
Generate CLI documentation for Docusaurus from Typer CLI application.

This script uses Typer's built-in help to generate markdown documentation
for all CLI commands and subcommands.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

OUTPUT_DIR = Path(__file__).parent.parent / "site" / "docs" / "cli"
CLI_COMMAND = "orchestrator"


def run_cli_help(command: List[str]) -> str:
    """Run CLI command with --help flag and return output."""
    try:
        result = subprocess.run(
            [CLI_COMMAND, *command, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout
    except FileNotFoundError:
        print(f"Error: '{CLI_COMMAND}' command not found")
        print("Make sure the CLI is installed: pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"Error running CLI help: {e}")
        sys.exit(1)


def parse_help_output(help_text: str) -> Dict[str, Any]:
    """Parse Typer help output into structured data."""
    lines = help_text.strip().split("\n")

    result = {
        "usage": "",
        "description": "",
        "commands": [],
        "arguments": [],
        "options": [],
    }

    current_section = None

    for line in lines:
        line_stripped = line.strip()

        if line.startswith("Usage:"):
            result["usage"] = line.replace("Usage:", "").strip()
        elif line.startswith("Commands:") or line.startswith("Options:") or line.startswith("Arguments:"):
            current_section = line_stripped.rstrip(":").lower()
        elif line_stripped and current_section:
            # Parse command/option/argument line
            if current_section == "commands":
                parts = line_stripped.split(maxsplit=1)
                if len(parts) == 2:
                    result["commands"].append({"name": parts[0], "description": parts[1]})
            elif current_section in ["options", "arguments"]:
                result[current_section].append(line_stripped)
        elif line_stripped and not current_section:
            # Description text
            if result["description"]:
                result["description"] += " " + line_stripped
            else:
                result["description"] = line_stripped

    return result


def generate_command_doc(command_path: List[str], help_data: Dict[str, Any]) -> str:
    """Generate markdown documentation for a command."""
    command_name = " ".join(command_path) if command_path else CLI_COMMAND

    md = f"## `{command_name}`\n\n"

    if help_data["description"]:
        md += f"{help_data['description']}\n\n"

    if help_data["usage"]:
        md += f"### Usage\n\n```bash\n{help_data['usage']}\n```\n\n"

    if help_data["arguments"]:
        md += "### Arguments\n\n"
        for arg in help_data["arguments"]:
            md += f"- `{arg}`\n"
        md += "\n"

    if help_data["options"]:
        md += "### Options\n\n"
        for opt in help_data["options"]:
            md += f"- `{opt}`\n"
        md += "\n"

    if help_data["commands"]:
        md += "### Subcommands\n\n"
        for cmd in help_data["commands"]:
            md += f"- **`{cmd['name']}`** - {cmd['description']}\n"
        md += "\n"

    return md


def generate_docs_recursive(command_path: List[str] = None) -> Dict[str, str]:
    """Recursively generate documentation for commands and subcommands."""
    if command_path is None:
        command_path = []

    docs = {}

    # Get help for current command
    help_text = run_cli_help(command_path)
    help_data = parse_help_output(help_text)

    # Generate doc for this command
    command_key = "-".join(command_path) if command_path else "index"
    docs[command_key] = generate_command_doc(command_path, help_data)

    # Recursively generate docs for subcommands
    for cmd in help_data["commands"]:
        subcommand_path = command_path + [cmd["name"]]
        subdocs = generate_docs_recursive(subcommand_path)
        docs.update(subdocs)

    return docs


def write_docs(docs: Dict[str, str]) -> None:
    """Write documentation files to output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for key, content in sorted(docs.items()):
        filename = f"{key}.md"
        filepath = OUTPUT_DIR / filename

        # Add frontmatter
        if key == "index":
            frontmatter = """---
sidebar_position: 1
title: CLI Commands
---

# CLI Commands

Complete command-line reference for the Kearney Data Platform orchestrator.

"""
        else:
            title = key.replace("-", " ").title()
            frontmatter = f"""---
sidebar_position: 100
title: {title}
---

# {title}

"""

        full_content = frontmatter + content

        filepath.write_text(full_content)
        print(f"Generated: {filepath}")


def main():
    """Main entry point."""
    print("Generating CLI documentation...")
    print(f"CLI command: {CLI_COMMAND}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Check if CLI is available
    try:
        subprocess.run([CLI_COMMAND, "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        print(f"\nError: '{CLI_COMMAND}' not found")
        print("Please install the CLI first: pip install -e .")
        sys.exit(1)

    # Generate docs
    print("\nDiscovering commands...")
    docs = generate_docs_recursive()

    print(f"\nFound {len(docs)} command groups")

    # Write docs
    write_docs(docs)

    print("\nCLI documentation generated successfully!")


if __name__ == "__main__":
    main()
