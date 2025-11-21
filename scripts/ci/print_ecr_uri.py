#!/usr/bin/env python3
"""
Print the ECR URI for the orchestrator API image.

This script retrieves the AWS account ID and constructs the full ECR URI
that can be used for App Runner deployment or other integrations.

Usage:
    python scripts/print_ecr_uri.py

Environment Variables:
    AWS_REGION: AWS region (default: us-east-1)
    ECR_REPOSITORY: ECR repository name (default: orchestrator-api)

Requires:
    - AWS CLI configured with valid credentials
    - Permissions for sts:GetCallerIdentity
"""

import os
import subprocess
import sys


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ECR_REPOSITORY = os.getenv("ECR_REPOSITORY", "orchestrator-api")


def main():
    try:
        account_id = subprocess.check_output(
            ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()

        ecr_uri = f"{account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPOSITORY}"
        print(ecr_uri)

    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get AWS account ID", file=sys.stderr)
        print(f"Make sure AWS CLI is configured with valid credentials", file=sys.stderr)
        if e.stderr:
            print(f"Details: {e.stderr.decode().strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: AWS CLI not found", file=sys.stderr)
        print("Please install AWS CLI: https://aws.amazon.com/cli/", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
