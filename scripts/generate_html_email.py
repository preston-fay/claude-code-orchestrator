#!/usr/bin/env python3
"""
Generate HTML Email from Markdown Report

Converts the markdown weekly report to a professional HTML email with:
- Kearney purple branding
- Inline CSS for email compatibility
- Responsive layout
- Tables and formatting
"""

import re
from pathlib import Path
from datetime import datetime


def parse_markdown_to_html(markdown_content: str) -> str:
    """
    Convert markdown report to HTML with Kearney styling

    Simple markdown parser for report structure
    """

    lines = markdown_content.split("\n")
    html_parts = []

    in_list = False
    current_section = None

    for line in lines:
        # Headers
        if line.startswith("# "):
            title = line[2:].strip()
            html_parts.append(
                f'<h1 style="color: #7823DC; font-size: 28px; margin: 20px 0 10px 0;">{title}</h1>'
            )

        elif line.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False

            section_title = line[3:].strip()
            current_section = section_title
            html_parts.append(
                f'<h2 style="color: #1E1E1E; font-size: 22px; margin: 30px 0 15px 0; border-bottom: 2px solid #7823DC; padding-bottom: 8px;">{section_title}</h2>'
            )

        elif line.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False

            subsection = line[4:].strip()
            html_parts.append(
                f'<h3 style="color: #5A1AA8; font-size: 18px; margin: 20px 0 10px 0;">{subsection}</h3>'
            )

        # Bold text (executive summary section headers)
        elif line.startswith("**Week of"):
            date_range = line.strip("*")
            html_parts.append(
                f'<p style="color: #A5A5A5; font-size: 16px; margin: 5px 0 20px 0;">{date_range}</p>'
            )

        # List items
        elif line.startswith("- "):
            if not in_list:
                html_parts.append(
                    '<ul style="list-style-type: none; padding-left: 0; margin: 10px 0;">'
                )
                in_list = True

            item = line[2:].strip()

            # Parse bold items in lists
            item = re.sub(r"\*\*(.*?)\*\*", r'<strong style="color: #1E1E1E;">\1</strong>', item)

            # Color code arrows
            if "↑" in item:
                item = item.replace("↑", '<span style="color: #7823DC;">↑</span>')
            if "↓" in item and "Change:" in item:
                # Check if it's a good or bad decline based on context
                item = item.replace("↓", '<span style="color: #A5A5A5;">↓</span>')
            if "→" in item:
                item = item.replace("→", '<span style="color: #A5A5A5;">→</span>')

            # Add metric styling for current/previous/change rows
            if item.startswith("<strong>Current:</strong>"):
                html_parts.append(
                    f'<li style="margin: 5px 0; padding: 8px; background-color: #F5F5F5; border-left: 4px solid #7823DC;">{item}</li>'
                )
            elif item.startswith("<strong>Rating:</strong>"):
                # Color code rating
                if "Elite" in item:
                    rating_color = "#7823DC"
                elif "High" in item:
                    rating_color = "#9B51E0"
                elif "Medium" in item:
                    rating_color = "#A5A5A5"
                else:
                    rating_color = "#666666"
                item_with_color = item.replace(
                    "Rating:</strong>",
                    f'Rating:</strong> <span style="color: {rating_color}; font-weight: bold;">',
                )
                html_parts.append(
                    f'<li style="margin: 5px 0; padding: 8px;">{item_with_color}</span></li>'
                )
            else:
                html_parts.append(f'<li style="margin: 5px 0; padding: 8px;">{item}</li>')

        # Horizontal rule
        elif line.strip() == "---":
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                '<hr style="border: none; border-top: 1px solid #E0E0E0; margin: 30px 0;">'
            )

        # Links
        elif line.startswith("["):
            if in_list:
                html_parts.append("</ul>")
                in_list = False

            # Parse markdown links
            link_match = re.match(r"\[([^\]]+)\]\(([^\)]+)\)", line.strip("- "))
            if link_match:
                link_text = link_match.group(1)
                link_url = link_match.group(2)
                html_parts.append(
                    f'<p style="margin: 5px 0;"><a href="{link_url}" style="color: #7823DC; text-decoration: none;">{link_text}</a></p>'
                )

        # Regular paragraphs
        elif line.strip().startswith("*") and not line.strip().startswith("**"):
            if in_list:
                html_parts.append("</ul>")
                in_list = False

            text = line.strip("*").strip()
            html_parts.append(
                f'<p style="color: #A5A5A5; font-size: 12px; font-style: italic; margin: 10px 0;">{text}</p>'
            )

        # Empty lines
        elif not line.strip():
            if in_list:
                html_parts.append("</ul>")
                in_list = False

    # Close any open list
    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


def generate_html_email(markdown_content: str) -> str:
    """
    Generate complete HTML email with Kearney branding
    """

    # Parse markdown to HTML
    body_html = parse_markdown_to_html(markdown_content)

    # Build complete email HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Weekly Metrics Report</title>
</head>
<body style="margin: 0; padding: 0; font-family: Inter, Arial, Helvetica, sans-serif; background-color: #F5F5F5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F5F5F5;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="margin: 0 auto; background-color: #FFFFFF; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #7823DC; color: #FFFFFF; padding: 30px 40px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: bold;">Weekly Metrics Report</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Claude Code Orchestrator</p>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 40px;">
                            {body_html}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #1E1E1E; color: #A5A5A5; padding: 20px 40px; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0 0 10px 0; font-size: 14px;">
                                <a href="https://github.com/preston-fay/claude-code-orchestrator" style="color: #7823DC; text-decoration: none;">View Repository</a>
                            </p>
                            <p style="margin: 0; font-size: 12px;">
                                This report was automatically generated by the Metrics Dashboard system.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    return html


def main():
    """Main entry point"""
    print("Generating HTML email from markdown report...")

    # Read markdown report
    report_path = Path("reports/weekly_report.md")

    if not report_path.exists():
        print(f"ERROR: Markdown report not found at {report_path}")
        # Create placeholder HTML
        html_content = generate_html_email(
            "# Weekly Metrics Report\n\n**Data not available**\n\nPlease run metrics collection workflow first."
        )
    else:
        with open(report_path, "r") as f:
            markdown_content = f.read()

        # Generate HTML
        html_content = generate_html_email(markdown_content)

    # Write HTML email
    html_path = Path("reports/weekly_report.html")
    with open(html_path, "w") as f:
        f.write(html_content)

    print(f"HTML email generated: {html_path}")
    print(f"HTML length: {len(html_content)} characters")


if __name__ == "__main__":
    main()
