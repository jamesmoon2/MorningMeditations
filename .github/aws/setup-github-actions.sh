#!/bin/bash
# Setup script for deploying GitHub Actions IAM resources

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Actions IAM Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
STACK_NAME="GitHubActions-MorningMeditations-IAM"
GITHUB_ORG="jamesmoon2"
GITHUB_REPO="MorningMeditations"
AWS_REGION="us-west-2"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEMPLATE_FILE="$SCRIPT_DIR/github-actions-iam.yml"

echo "Configuration:"
echo "  Stack Name: $STACK_NAME"
echo "  GitHub Org: $GITHUB_ORG"
echo "  GitHub Repo: $GITHUB_REPO"
echo "  AWS Region: $AWS_REGION"
echo "  Template: $TEMPLATE_FILE"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if user is authenticated
echo "Verifying AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ Authenticated as AWS Account: $ACCOUNT_ID${NC}"
echo ""

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: Template file not found: $TEMPLATE_FILE${NC}"
    exit 1
fi

# Check if stack already exists
echo "Checking if stack already exists..."
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" &> /dev/null; then
    echo -e "${YELLOW}Stack already exists. Updating...${NC}"
    OPERATION="update"

    aws cloudformation update-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_FILE" \
        --parameters \
            ParameterKey=GitHubOrg,ParameterValue="$GITHUB_ORG" \
            ParameterKey=GitHubRepo,ParameterValue="$GITHUB_REPO" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION"

    echo "Waiting for stack update to complete..."
    aws cloudformation wait stack-update-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
else
    echo "Creating new stack..."
    OPERATION="create"

    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_FILE" \
        --parameters \
            ParameterKey=GitHubOrg,ParameterValue="$GITHUB_ORG" \
            ParameterKey=GitHubRepo,ParameterValue="$GITHUB_REPO" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION"

    echo "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
fi

echo -e "${GREEN}✓ Stack ${OPERATION}d successfully!${NC}"
echo ""

# Get outputs
echo "Retrieving stack outputs..."
ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='RoleArn'].OutputValue" \
    --output text \
    --region "$AWS_REGION")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "IAM Role ARN: $ROLE_ARN"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Go to your GitHub repository settings:"
echo "   https://github.com/$GITHUB_ORG/$GITHUB_REPO/settings/secrets/actions"
echo ""
echo "2. Add a new repository secret:"
echo "   Name:  AWS_ROLE_ARN"
echo "   Value: $ROLE_ARN"
echo ""
echo "3. Create a GitHub environment (optional but recommended):"
echo "   - Go to Settings > Environments > New environment"
echo "   - Name: production"
echo "   - Add protection rules (e.g., required reviewers)"
echo ""
echo -e "${GREEN}Your CI/CD pipeline is now ready!${NC}"
