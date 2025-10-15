#!/usr/bin/env python3
"""
Generate design token documentation for Docusaurus.

This script reads design_system/tokens.json and generates markdown
documentation with visual examples.
"""

import json
from pathlib import Path
from typing import Any, Dict

TOKENS_FILE = Path(__file__).parent.parent / "design_system" / "tokens.json"
OUTPUT_DIR = Path(__file__).parent.parent / "site" / "docs" / "design-system"


def load_tokens() -> Dict[str, Any]:
    """Load design tokens from JSON file."""
    with open(TOKENS_FILE) as f:
        return json.load(f)


def generate_color_table(colors: Dict[str, str], title: str) -> str:
    """Generate HTML table for color tokens."""
    html = f"### {title}\n\n"
    html += "<table>\n"
    html += "  <thead>\n"
    html += "    <tr>\n"
    html += "      <th>Token</th>\n"
    html += "      <th>Value</th>\n"
    html += "      <th>Preview</th>\n"
    html += "    </tr>\n"
    html += "  </thead>\n"
    html += "  <tbody>\n"

    for name, value in colors.items():
        html += "    <tr>\n"
        html += f"      <td><code>{name}</code></td>\n"
        html += f"      <td><code>{value}</code></td>\n"
        html += f'      <td><div style="width: 50px; height: 30px; background-color: {value}; border: 1px solid var(--kearney-border);"></div></td>\n'
        html += "    </tr>\n"

    html += "  </tbody>\n"
    html += "</table>\n\n"
    return html


def generate_typography_doc(typography: Dict[str, Any]) -> str:
    """Generate typography documentation."""
    md = """---
sidebar_position: 2
title: Typography
---

# Typography

Typography system for the Kearney Data Platform.

## Font Family

"""

    md += f"Primary: `{typography['fontFamily']['primary']}`\n\n"
    md += f"Monospace: `{typography['fontFamily']['mono']}`\n\n"

    md += "## Font Weights\n\n"
    md += "<table>\n"
    md += "  <thead><tr><th>Name</th><th>Value</th><th>Preview</th></tr></thead>\n"
    md += "  <tbody>\n"
    for name, value in typography["fontWeight"].items():
        md += f'    <tr><td><code>{name}</code></td><td><code>{value}</code></td><td style="font-weight: {value};">The quick brown fox</td></tr>\n'
    md += "  </tbody>\n"
    md += "</table>\n\n"

    md += "## Type Scale\n\n"
    md += f"Base size: {typography['scale']['base']}px\n\n"
    md += f"Ratio: {typography['scale']['ratio']}\n\n"

    md += "<table>\n"
    md += "  <thead><tr><th>Size</th><th>Value</th><th>Preview</th></tr></thead>\n"
    md += "  <tbody>\n"
    for name, value in typography["sizes"].items():
        md += f'    <tr><td><code>{name}</code></td><td><code>{value}</code></td><td style="font-size: {value};">Aa</td></tr>\n'
    md += "  </tbody>\n"
    md += "</table>\n\n"

    md += "## Line Height\n\n"
    for name, value in typography["lineHeight"].items():
        md += f"- **{name}**: `{value}`\n"
    md += "\n"

    md += "## Letter Spacing\n\n"
    for name, value in typography["letterSpacing"].items():
        md += f"- **{name}**: `{value}`\n"
    md += "\n"

    return md


def generate_color_doc(tokens: Dict[str, Any]) -> str:
    """Generate color documentation."""
    md = """---
sidebar_position: 1
title: Colors
---

# Colors

Color system for the Kearney Data Platform.

## Core Palette

The core Kearney brand colors.

"""

    md += generate_color_table(tokens["palette"]["core"], "Core Colors")

    md += "## Extended Palette\n\n"
    md += "Extended grayscale and utility colors.\n\n"

    md += generate_color_table(tokens["palette"]["extended"], "Extended Colors")

    md += "## Theme - Light Mode\n\n"
    md += "Semantic color tokens for light theme.\n\n"

    md += generate_color_table(tokens["theme"]["light"], "Light Theme")

    md += "## Theme - Dark Mode\n\n"
    md += "Semantic color tokens for dark theme.\n\n"

    md += generate_color_table(tokens["theme"]["dark"], "Dark Theme")

    return md


def generate_spacing_doc(spacing: Dict[str, Any]) -> str:
    """Generate spacing documentation."""
    md = """---
sidebar_position: 3
title: Spacing
---

# Spacing

Spacing system for the Kearney Data Platform.

## Scale

Modular scale: {scale}

## Values

""".format(scale=spacing["scale"])

    md += "<table>\n"
    md += "  <thead><tr><th>Token</th><th>Value</th><th>Preview</th></tr></thead>\n"
    md += "  <tbody>\n"
    for name, value in spacing["values"].items():
        md += f'    <tr><td><code>{name}</code></td><td><code>{value}</code></td><td><div style="width: {value}; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>\n'
    md += "  </tbody>\n"
    md += "</table>\n\n"

    return md


def generate_overview_doc(tokens: Dict[str, Any]) -> str:
    """Generate overview documentation."""
    meta = tokens.get("meta", {})

    md = """---
sidebar_position: 0
title: Design System Overview
---

# Design System Overview

The Kearney Data Platform design system provides a comprehensive set of design tokens
for building brand-compliant interfaces.

## Principles

"""

    md += "### Brand Constraints\n\n"
    md += f"- **No Emojis**: {meta.get('no_emojis', False)}\n"
    md += f"- **No Gridlines**: {meta.get('no_gridlines', False)}\n"
    md += f"- **Label First**: {meta.get('label_first', False)}\n"
    md += f"- **Spot Color Emphasis**: {meta.get('spot_color_emphasis', False)}\n\n"

    md += "### Typography\n\n"
    md += f"{meta.get('typography_note', '')}\n\n"

    md += """## Token Categories

The design system includes the following token categories:

1. **Colors** - Core palette, extended colors, and semantic theme tokens
2. **Typography** - Font families, weights, sizes, and scales
3. **Spacing** - Consistent spacing values based on modular scale
4. **Border Radius** - Rounded corner values
5. **Shadows** - Elevation and depth effects

## Usage

### In CSS

```css
:root {
  --kearney-purple: #7823DC;
  --kearney-charcoal: #1E1E1E;
}

.button {
  background-color: var(--kearney-purple);
  color: var(--kearney-white);
  padding: var(--spacing-4);
  border-radius: var(--border-radius-base);
}
```

### In JavaScript/TypeScript

```typescript
import tokens from './design_system/tokens.json';

const primaryColor = tokens.theme.light.emphasis;
const headingFont = tokens.typography.fontFamily.primary;
```

### In React

```tsx
import { getThemeColors } from './design-system/tokens';

const theme = getThemeColors('light');

<div style={{
  backgroundColor: theme.background,
  color: theme.text
}}>
  Content
</div>
```

## Version

"""

    md += f"Design system version: **{meta.get('version', 'N/A')}**\n\n"
    md += f"Source: {meta.get('source', 'N/A')}\n\n"

    return md


def main():
    """Main entry point."""
    print("Generating design token documentation...")
    print(f"Tokens file: {TOKENS_FILE}")
    print(f"Output directory: {OUTPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load tokens
    tokens = load_tokens()

    # Generate documentation files
    files = {
        "index.md": generate_overview_doc(tokens),
        "colors.md": generate_color_doc(tokens),
        "typography.md": generate_typography_doc(tokens["typography"]),
        "spacing.md": generate_spacing_doc(tokens["spacing"]),
    }

    for filename, content in files.items():
        filepath = OUTPUT_DIR / filename
        filepath.write_text(content)
        print(f"Generated: {filepath}")

    print("\nDesign token documentation generated successfully!")


if __name__ == "__main__":
    main()
