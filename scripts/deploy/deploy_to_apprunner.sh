#!/usr/bin/env bash
#
# Deploy to App Runner Helper Script
#
# This script prints all the information needed to deploy the
# Orchestrator API to AWS App Runner via the AWS Console.
#
# Usage:
#   ./scripts/deploy_to_apprunner.sh
#
# Environment Variables:
#   AWS_REGION      - AWS region (default: us-east-1)
#   ECR_REPOSITORY  - ECR repository name (default: orchestrator-api)
#

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REPOSITORY=${ECR_REPOSITORY:-orchestrator-api}

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ -z "$ACCOUNT_ID" ]; then
    echo "Error: Could not retrieve AWS Account ID"
    echo "Make sure AWS CLI is configured with valid credentials"
    exit 1
fi

ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo "=============================================="
echo "   AWS App Runner Deployment Guide"
echo "=============================================="
echo ""
echo "ECR Image URI:"
echo ""
echo "    ${ECR_URI}:latest"
echo ""
echo "----------------------------------------------"
echo "Deployment Steps:"
echo "----------------------------------------------"
echo ""
echo "1. Login to AWS Console"
echo "   https://console.aws.amazon.com/apprunner"
echo ""
echo "2. Click 'Create service'"
echo ""
echo "3. Configure Source:"
echo "   - Source type: Container registry"
echo "   - Provider: Amazon ECR"
echo "   - Image URI: ${ECR_URI}"
echo "   - Tag: latest"
echo ""
echo "4. Configure Deployment:"
echo "   - Enable: 'Deploy new image versions automatically'"
echo ""
echo "5. Configure Service:"
echo "   - Port: 8000"
echo "   - CPU: 1 vCPU"
echo "   - Memory: 2 GB"
echo ""
echo "6. Configure Health Check:"
echo "   - Protocol: HTTP"
echo "   - Path: /health"
echo ""
echo "7. Add Environment Variables:"
echo "   - WORKSPACE_BASE=/mnt/workspaces"
echo "   - ORCHESTRATOR_ENV=production"
echo "   - AWS_REGION=${AWS_REGION}"
echo "   - LOG_LEVEL=info"
echo ""
echo "8. Click 'Create & deploy'"
echo ""
echo "----------------------------------------------"
echo "After Deployment:"
echo "----------------------------------------------"
echo ""
echo "App Runner will provide a public URL like:"
echo "   https://xxxxxxxxxx.${AWS_REGION}.awsapprunner.com"
echo ""
echo "Test with:"
echo "   curl https://your-url.awsapprunner.com/health"
echo ""
echo "=============================================="
echo "For detailed instructions, see:"
echo "   DEPLOYMENT_APP_RUNNER.md"
echo "=============================================="
