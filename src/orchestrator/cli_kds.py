"""CLI tool to print and verify Kearney Design System tokens."""

import json
import sys
from src.orchestrator.design import load_kearney_tokens, get_token_version, BrandTokensError


def main() -> None:
    """
    Print KDS tokens as JSON.

    This command loads the active Kearney Design System tokens and outputs
    them as formatted JSON. Useful for:
    - Verifying token values
    - Debugging design issues
    - Confirming token version
    - Validating token integrity

    Exit codes:
        0: Success - tokens loaded and printed
        1: Error - tokens could not be loaded

    Environment:
        KDS_TOKENS_JSON: Optional JSON override for emergency hotfixes

    Examples:
        $ kds-print
        {
          "meta": {
            "name": "Kearney",
            "version": "1.0.0",
            ...
          },
          "colors": {
            "primary": "#7823DC",
            ...
          }
        }

        $ kds-print | jq '.colors.primary'
        "#7823DC"
    """
    try:
        # Load tokens
        tokens = load_kearney_tokens()

        # Print formatted JSON
        print(json.dumps(tokens, indent=2, sort_keys=False))

        # Exit success
        sys.exit(0)

    except BrandTokensError as e:
        print(f"ERROR: Failed to load Kearney Design System tokens", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Check that kearney_brand.yml exists and is valid YAML.", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def version() -> None:
    """
    Print KDS token version only.

    Examples:
        $ kds-version
        1.0.0
    """
    try:
        ver = get_token_version()
        print(ver)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
