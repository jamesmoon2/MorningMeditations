# AWS IAM Setup for GitHub Actions

This directory contains AWS IAM resources for GitHub Actions OIDC authentication.

## Quick Start

Run the automated setup script:

```bash
.github/aws/setup-github-actions.sh
```

This will:
1. Create GitHub OIDC provider in AWS (if not exists)
2. Create IAM role: `GitHubActions-MorningMeditations-Deploy`
3. Output the Role ARN for GitHub configuration

## Files

- **`github-actions-iam.yml`**: CloudFormation template for IAM resources
- **`setup-github-actions.sh`**: Automated deployment script
- **`README.md`**: This file

## Manual Setup

If you prefer to set up manually:

```bash
aws cloudformation create-stack \
  --stack-name GitHubActions-MorningMeditations-IAM \
  --template-body file://.github/aws/github-actions-iam.yml \
  --parameters \
    ParameterKey=GitHubOrg,ParameterValue=jamesmoon2 \
    ParameterKey=GitHubRepo,ParameterValue=MorningMeditations \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

## After Setup

Add the Role ARN to GitHub:

1. Get the ARN:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name GitHubActions-MorningMeditations-IAM \
     --query "Stacks[0].Outputs[?OutputKey=='RoleArn'].OutputValue" \
     --output text
   ```

2. Add to GitHub:
   - Go to: https://github.com/jamesmoon2/MorningMeditations/settings/secrets/actions
   - Secret Name: `AWS_ROLE_ARN`
   - Secret Value: (paste ARN from above)

## Resources Created

- **OIDC Provider**: `token.actions.githubusercontent.com`
- **IAM Role**: `GitHubActions-MorningMeditations-Deploy`
- **Permissions**: PowerUserAccess + CDK IAM permissions

## Security

- Uses OIDC (no long-lived credentials)
- Role can only be assumed by:
  - GitHub Actions
  - From `jamesmoon2/MorningMeditations` repository
  - From `main` or `claude/**` branches

## Cleanup

To remove all resources:

```bash
aws cloudformation delete-stack \
  --stack-name GitHubActions-MorningMeditations-IAM \
  --region us-west-2
```

For more details, see [../../CICD.md](../../CICD.md)
