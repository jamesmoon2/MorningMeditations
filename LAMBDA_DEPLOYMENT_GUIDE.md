# Lambda Deployment Guide

Quick reference for deploying Lambda function updates.

## When You Edit Lambda Code

Anytime you modify files in the `lambda/` directory (handler.py, email_formatter.py, themes.py, etc.), follow these steps:

### Step 1: Rebuild the Lambda Package

Run the build script to copy your updated code and ensure Linux-compatible dependencies:

```powershell
cd MorningMeditations
powershell -ExecutionPolicy Bypass -File build_lambda.ps1
```

This script:
- Cleans the `lambda_linux` directory
- Copies your Lambda Python files from `lambda/` to `lambda_linux/`
- Installs Linux-compatible dependencies into `lambda_linux/`

### Step 2: Deploy to AWS

Deploy the updated Lambda function with CDK:

```powershell
cdk deploy
```

CDK will:
- Detect the changes in `lambda_linux/`
- Package and upload the new Lambda code
- Update the Lambda function
- Complete in ~30-40 seconds

### Step 3: Test (Optional)

Test the updated Lambda function manually:

```powershell
aws lambda invoke --function-name DailyStoicSender --region us-east-1 response.json
```

Then check the response:

```powershell
cat response.json
```

## Quick Command Reference

### Full Update Flow
```powershell
# Navigate to project
cd MorningMeditations

# Rebuild Lambda package
powershell -ExecutionPolicy Bypass -File build_lambda.ps1

# Deploy to AWS
cdk deploy

# Test (optional)
aws lambda invoke --function-name DailyStoicSender --region us-east-1 response.json
cat response.json
```

### View Recent Logs
```powershell
$startTime = [DateTimeOffset]::Now.AddMinutes(-10).ToUnixTimeMilliseconds()
aws logs filter-log-events --log-group-name /aws/lambda/DailyStoicSender --region us-east-1 --start-time $startTime
```

## When to Rebuild vs Just Deploy

**Always rebuild** when:
- You edit any `.py` files in `lambda/`
- You modify `lambda/requirements.txt`
- You want to ensure you have the latest dependencies

**You can skip rebuilding** when:
- You only change infrastructure (CDK stack code in `infra/`)
- You modify `cdk.json` configuration
- You update IAM permissions or EventBridge rules

## Common Issues

### Issue: "Module not found" error after deployment
**Solution**: You forgot to rebuild. Run the build script, then deploy again.

### Issue: Lambda still using old code
**Solution**: CDK caches unchanged code. Force rebuild:
```powershell
Remove-Item -Recurse -Force lambda_linux
powershell -ExecutionPolicy Bypass -File build_lambda.ps1
cdk deploy
```

### Issue: Build script fails
**Cause**: Usually pip or Python environment issues
**Solution**: 
1. Ensure virtual environment is activated: `.venv\Scripts\activate`
2. Update pip: `pip install --upgrade pip`
3. Try build script again

## Notes

- The `lambda/` directory is your **source code** - edit files here
- The `lambda_linux/` directory is **generated** - don't edit files here
- Always test locally before deploying if possible
- The build script takes ~10-15 seconds
- CDK deployment takes ~30-40 seconds for Lambda updates


