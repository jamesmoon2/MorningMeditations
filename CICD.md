# CI/CD Pipeline Documentation

Automated Continuous Integration and Continuous Deployment pipeline for MorningMeditations using GitHub Actions and AWS.

## Overview

This project uses GitHub Actions for CI/CD with AWS IAM OIDC authentication for secure, keyless deployment to AWS.

### Pipelines

1. **CI Pipeline** (`.github/workflows/ci.yml`)
   - Runs on: Pull requests and pushes to `main` and `claude/**` branches
   - Purpose: Test code quality, run tests, validate configuration
   - Duration: ~3-5 minutes

2. **CD Pipeline** (`.github/workflows/deploy.yml`)
   - Runs on: Pushes to `main` branch (can be manually triggered)
   - Purpose: Deploy CDK stack to AWS production environment
   - Duration: ~5-10 minutes

## Architecture

```
GitHub Actions
    ↓ (OIDC Authentication)
AWS IAM Role (GitHubActions-MorningMeditations-Deploy)
    ↓ (AssumeRole)
AWS Services
    ├── CloudFormation (CDK deployments)
    ├── Lambda (function updates)
    ├── S3 (config file uploads)
    ├── EventBridge (schedule rules)
    └── SES (email service)
```

## Initial Setup

### Prerequisites

- AWS Account with administrative access
- GitHub repository with admin permissions
- AWS CLI installed and configured
- Git installed

### Step 1: Deploy AWS IAM Resources

The IAM resources must be set up once before the CI/CD pipeline can work.

#### Option A: Automated Setup (Recommended)

```bash
# Navigate to the project root
cd MorningMeditations

# Run the setup script
.github/aws/setup-github-actions.sh
```

The script will:
1. Create GitHub OIDC provider in your AWS account (if it doesn't exist)
2. Create an IAM role with necessary permissions
3. Output the Role ARN for GitHub configuration

#### Option B: Manual Setup via AWS Console

1. **Deploy CloudFormation Stack**:
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

2. **Wait for completion**:
   ```bash
   aws cloudformation wait stack-create-complete \
     --stack-name GitHubActions-MorningMeditations-IAM \
     --region us-west-2
   ```

3. **Get the Role ARN**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name GitHubActions-MorningMeditations-IAM \
     --query "Stacks[0].Outputs[?OutputKey=='RoleArn'].OutputValue" \
     --output text
   ```

### Step 2: Configure GitHub Repository Secrets

1. **Navigate to GitHub Secrets**:
   - Go to: `https://github.com/jamesmoon2/MorningMeditations/settings/secrets/actions`

2. **Add Repository Secret**:
   - Click: "New repository secret"
   - Name: `AWS_ROLE_ARN`
   - Value: `arn:aws:iam::XXXXXXXXXXXX:role/GitHubActions-MorningMeditations-Deploy`
     (Use the ARN from Step 1)
   - Click: "Add secret"

### Step 3: Create GitHub Environment (Optional but Recommended)

Environments add an extra layer of protection for production deployments.

1. **Navigate to Environments**:
   - Go to: `https://github.com/jamesmoon2/MorningMeditations/settings/environments`

2. **Create Production Environment**:
   - Click: "New environment"
   - Name: `production`
   - Click: "Configure environment"

3. **Add Protection Rules** (optional):
   - ✓ Required reviewers: Add yourself or team members
   - ✓ Wait timer: Add a delay before deployment (e.g., 5 minutes)
   - ✓ Deployment branches: Restrict to `main` branch only

4. **Save**

## CI Pipeline Details

### Triggers

- Pull requests targeting `main` or `claude/**` branches
- Direct pushes to `main` or `claude/**` branches

### Jobs

#### 1. Test Job
- **Purpose**: Validate code quality and functionality
- **Steps**:
  1. Checkout code
  2. Set up Python 3.12
  3. Set up Node.js 18 for CDK
  4. Install dependencies
  5. Run Black (code formatting check)
  6. Run Flake8 (linting)
  7. Run MyPy (type checking) - non-blocking
  8. Run Pytest (unit tests with coverage)
  9. Validate quotes JSON file
  10. Run quote loader tests
  11. CDK synth (validate infrastructure code)

#### 2. YAML Lint Job
- **Purpose**: Ensure workflow files are valid
- **Steps**:
  1. Checkout code
  2. Lint all YAML files in `.github/workflows/`

### Success Criteria

All checks must pass for the CI pipeline to succeed:
- ✓ Code is properly formatted (Black)
- ✓ No linting errors (Flake8)
- ✓ All tests pass (Pytest)
- ✓ Quotes JSON is valid
- ✓ CDK synthesizes successfully
- ✓ YAML files are valid

## CD Pipeline Details

### Triggers

- Automatic: Pushes to `main` branch
- Manual: `workflow_dispatch` event (via GitHub Actions UI)

### Permissions

Uses OIDC to assume AWS IAM role - no long-lived credentials stored in GitHub.

### Jobs

#### Deploy Job
- **Environment**: `production` (requires environment setup)
- **Steps**:
  1. Checkout code
  2. Set up Python 3.12
  3. Set up Node.js 18
  4. Install dependencies
  5. Install AWS CDK CLI
  6. Configure AWS credentials (OIDC)
  7. Verify AWS identity
  8. Bootstrap CDK (if needed)
  9. Run CDK diff (show changes)
  10. Deploy CDK stack
  11. Get S3 bucket name from outputs
  12. Upload configuration files to S3
  13. Generate deployment summary

### Deployment Behavior

#### Configuration Files Upload

The pipeline intelligently handles configuration files:

- **`stoic_quotes_365_days.json`**: Always uploaded (may have updates)
- **`recipients.json`**: Only uploaded if not already in S3 (preserve production data)
- **`quote_history.json`**: Only uploaded if not already in S3 (preserve history)

This prevents accidentally overwriting production recipient lists or historical data.

### Success Criteria

- ✓ AWS authentication successful
- ✓ CDK stack deployed without errors
- ✓ Configuration files uploaded
- ✓ All Lambda functions updated
- ✓ EventBridge schedule active

## IAM Permissions

The GitHub Actions IAM role has the following permissions:

### Managed Policies
- **PowerUserAccess**: Full access to AWS services except IAM

### Custom Policies

#### CDK IAM Permissions
Allows CDK to create/manage IAM roles and policies for the application:
- Create, update, delete IAM roles with prefix `DailyStoicStack-*` or `cdk-*`
- Attach/detach policies to those roles
- Create/delete IAM policies with same prefix
- Pass roles to AWS services

### Security Considerations

1. **OIDC Authentication**: No long-lived AWS credentials stored in GitHub
2. **Role Assumption Conditions**:
   - Must be from GitHub Actions (`sts.amazonaws.com` audience)
   - Must be from `jamesmoon2/MorningMeditations` repository
   - Only from `main` or `claude/**` branches
3. **Scoped Permissions**: IAM role limited to specific resource prefixes
4. **Environment Protection**: Production environment can require approvals

## Troubleshooting

### CI Pipeline Failures

#### Black Formatting Errors
```bash
# Fix locally
black .

# Commit and push
git add .
git commit -m "Fix code formatting"
git push
```

#### Flake8 Linting Errors
Check the error output and fix the specific issues. Common fixes:
```bash
# Check what needs fixing
flake8 .

# Fix automatically where possible
autopep8 --in-place --aggressive --aggressive .
```

#### Test Failures
```bash
# Run tests locally
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=lambda --cov-report=html

# Open coverage report
open htmlcov/index.html
```

#### CDK Synth Failures
```bash
# Try synthesizing locally
cdk synth

# Common issues:
# - Missing dependencies in requirements.txt
# - Syntax errors in infra/stoic_stack.py
# - Missing context values in cdk.json
```

### CD Pipeline Failures

#### AWS Authentication Failed
- Verify `AWS_ROLE_ARN` secret is set correctly in GitHub
- Ensure IAM role exists and has correct trust policy
- Check IAM role permissions

```bash
# Verify IAM role exists
aws iam get-role --role-name GitHubActions-MorningMeditations-Deploy

# Check trust policy
aws iam get-role --role-name GitHubActions-MorningMeditations-Deploy \
  --query 'Role.AssumeRolePolicyDocument'
```

#### CDK Deployment Failed
- Check CloudWatch Logs in GitHub Actions output
- Verify AWS account has sufficient permissions
- Ensure CDK is bootstrapped in the region

```bash
# Check bootstrap stack
aws cloudformation describe-stacks --stack-name CDKToolkit --region us-west-2

# Re-bootstrap if needed
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/us-west-2
```

#### S3 Upload Failed
- Verify bucket exists (created by CDK)
- Check IAM role has S3 permissions
- Verify configuration files exist in `config/` directory

```bash
# List buckets
aws s3 ls | grep daily-stoic

# Check bucket contents
aws s3 ls s3://YOUR-BUCKET-NAME/ --recursive
```

### Viewing Logs

#### GitHub Actions Logs
1. Go to: `https://github.com/jamesmoon2/MorningMeditations/actions`
2. Click on the workflow run
3. Click on the job name
4. Expand the step to see detailed logs

#### AWS CloudWatch Logs
```bash
# View CDK deployment logs
aws cloudformation describe-stack-events \
  --stack-name DailyStoicStack \
  --region us-west-2

# View Lambda function logs
aws logs tail /aws/lambda/DailyStoicSender --follow --region us-west-2
```

## Manual Operations

### Manual Deployment Trigger

You can manually trigger a deployment from GitHub:

1. Go to: `https://github.com/jamesmoon2/MorningMeditations/actions/workflows/deploy.yml`
2. Click: "Run workflow"
3. Select branch: `main`
4. Click: "Run workflow"

### Update Configuration Files

To update recipients or quotes without a full deployment:

```bash
# Update recipients
aws s3 cp config/recipients.json s3://YOUR-BUCKET-NAME/recipients.json

# Update quotes database
aws s3 cp config/stoic_quotes_365_days.json s3://YOUR-BUCKET-NAME/config/stoic_quotes_365_days.json

# View history
aws s3 cp s3://YOUR-BUCKET-NAME/quote_history.json -
```

### Destroy Stack (CAUTION)

To completely remove the deployed infrastructure:

```bash
# Via CDK (recommended)
cdk destroy

# Via AWS CLI
aws cloudformation delete-stack --stack-name DailyStoicStack --region us-west-2

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name DailyStoicStack --region us-west-2
```

### Remove GitHub Actions IAM Resources

To remove the GitHub Actions IAM resources (when no longer needed):

```bash
aws cloudformation delete-stack \
  --stack-name GitHubActions-MorningMeditations-IAM \
  --region us-west-2
```

## Development Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make changes and test locally**:
   ```bash
   # Run tests
   pytest tests/ -v

   # Check formatting
   black .

   # Validate infrastructure
   cdk synth
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/my-new-feature
   ```

4. **Create Pull Request**:
   - Go to GitHub
   - Create PR from your branch to `main`
   - CI pipeline will run automatically
   - Review checks and address any failures

5. **Merge to main**:
   - Once CI passes and PR is approved
   - Merge to `main`
   - CD pipeline will automatically deploy

### Testing Pipeline Changes

To test changes to the GitHub Actions workflows themselves:

1. Create a test branch starting with `claude/`:
   ```bash
   git checkout -b claude/test-pipeline-changes
   ```

2. Make changes to workflow files

3. Push and observe:
   ```bash
   git push origin claude/test-pipeline-changes
   ```

4. CI will run on the branch, but CD will not deploy (safety feature)

## Monitoring

### GitHub Actions Dashboard

Monitor all workflow runs:
- URL: `https://github.com/jamesmoon2/MorningMeditations/actions`
- Shows: All workflow runs, status, duration, logs

### AWS Resources

Monitor deployed resources:

```bash
# Stack status
aws cloudformation describe-stacks --stack-name DailyStoicStack --region us-west-2

# Lambda function status
aws lambda get-function --function-name DailyStoicSender --region us-west-2

# Recent Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=DailyStoicSender \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --region us-west-2
```

### Costs

Expected monthly costs:
- **GitHub Actions**: Free (within free tier limits)
- **AWS**: ~$0.18/month (primarily Anthropic API costs)

Monitor AWS costs:
```bash
# View current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=SERVICE
```

## Security Best Practices

1. **Never commit AWS credentials** to the repository
2. **Use OIDC authentication** (not long-lived access keys)
3. **Limit IAM role permissions** to minimum necessary
4. **Use GitHub environments** for production deployments
5. **Enable branch protection** on `main` branch
6. **Require pull request reviews** before merging
7. **Keep dependencies updated** (Dependabot)
8. **Monitor CloudWatch logs** for suspicious activity

## Advanced Configuration

### Changing Deployment Region

To deploy to a different AWS region:

1. Update `app.py`:
   ```python
   env=cdk.Environment(region="us-east-1")  # Change region
   ```

2. Update workflow environment variables in `.github/workflows/deploy.yml`:
   ```yaml
   env:
     AWS_REGION: us-east-1  # Change region
   ```

3. Re-deploy IAM resources in new region if needed

### Adding Multiple Environments

To add staging/development environments:

1. Create separate CDK stacks:
   ```python
   # In app.py
   StoicStack(app, "DailyStoicStack-Staging", ...)
   StoicStack(app, "DailyStoicStack-Production", ...)
   ```

2. Create separate GitHub environments and workflows
3. Use different configuration files per environment

### Customizing CI Checks

Edit `.github/workflows/ci.yml` to add/remove checks:

```yaml
# Example: Add security scanning
- name: Security scan
  run: bandit -r lambda/ -f json -o bandit-report.json
```

## Support and Resources

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **AWS CDK Docs**: https://docs.aws.amazon.com/cdk/
- **AWS OIDC for GitHub**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- **Project Documentation**: See [README.md](README.md), [DEPLOYMENT.md](DEPLOYMENT.md)

---

**CI/CD Pipeline is now fully configured and ready to use!**
