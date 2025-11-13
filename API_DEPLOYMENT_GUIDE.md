# API Deployment Guide

This guide walks you through deploying the new Morning Reflections API to AWS.

## What's Been Built

### New Components

1. **API Lambda Function** (`lambda/api_handler.py`)
   - Read-only Lambda that serves reflections from S3
   - Returns JSON responses for hardware device integration
   - Fast response time (~100ms) - just reads from S3

2. **API Gateway REST API**
   - Public endpoints (no authentication required)
   - Rate limiting: 10 burst, 5 requests/second
   - CORS enabled for hardware device access
   - Two endpoints:
     - `GET /reflection/today` - Today's reflection
     - `GET /reflection/{date}` - Specific date (YYYY-MM-DD)

3. **Build Script** (`build_lambda.sh`)
   - Bash script to package Lambda code with Linux dependencies
   - Creates `lambda_linux/` directory for deployment

### Updated Infrastructure

- **CDK Stack** (`infra/stoic_stack.py`)
  - Added API Gateway REST API
  - Added new Lambda function for API
  - Configured throttling and CORS
  - Added CloudFormation outputs for API URLs

## Prerequisites

Before deploying, ensure you have:

- ✅ AWS CLI installed and configured with credentials
- ✅ AWS CDK CLI installed (`npm install -g aws-cdk`)
- ✅ Python 3.12+ installed
- ✅ Access to the AWS account where the existing stack is deployed

## Deployment Steps

### Step 1: Build Lambda Package

From the project root directory:

```bash
# Make the build script executable (if not already)
chmod +x build_lambda.sh

# Build the Lambda package
./build_lambda.sh
```

This will:
- Create `lambda_linux/` directory
- Copy all Python files from `lambda/` including the new `api_handler.py`
- Install dependencies for Linux (required for Lambda)

### Step 2: Deploy Infrastructure

Deploy the updated CDK stack:

```bash
# Synthesize CloudFormation template (optional, for review)
cdk synth

# Deploy to AWS
cdk deploy

# When prompted, review changes and type 'y' to approve
```

The deployment will:
- Create a new Lambda function: `ReflectionApiHandler`
- Create API Gateway REST API: "Morning Reflections API"
- Configure endpoints, rate limiting, and CORS
- Output the API URLs

### Step 3: Verify Deployment

After deployment completes, CDK will output important values:

```
Outputs:
DailyStoicStack.ApiUrl = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
DailyStoicStack.ApiTodayEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/reflection/today
DailyStoicStack.ApiDateEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/reflection/{date}
```

**Save these URLs!** You'll need them for the hardware device.

### Step 4: Test the API

Test with curl or any HTTP client:

```bash
# Get today's reflection
curl https://YOUR_API_URL/reflection/today

# Get a specific date's reflection
curl https://YOUR_API_URL/reflection/2025-01-10
```

Expected response:

```json
{
  "date": "2025-01-15",
  "quote": "You have power over your mind - not outside events...",
  "attribution": "Marcus Aurelius, Meditations, Book 5",
  "theme": "Self-Mastery",
  "reflection": "In our modern world of constant notifications...",
  "monthlyTheme": {
    "name": "Discipline and Self-Improvement",
    "description": "Focus on building habits, self-control, and starting fresh"
  }
}
```

## Important Notes

### Rate Limiting

The API is configured with:
- **Burst limit**: 10 concurrent requests
- **Rate limit**: 5 requests per second

This is more than sufficient for <100 calls/day from a hardware device.

### Cost Impact

Adding the API will increase monthly costs by approximately:
- **API Gateway**: $0 (first 1M requests free)
- **Lambda**: ~$0.20 per million requests (negligible at <100/day)
- **S3 reads**: Negligible (already storing data)

**Total additional cost: ~$0.00-$0.01/month** at your expected volume.

### Security

The API is currently **public** (no authentication). This is acceptable for read-only access to non-sensitive content. If you want to add authentication later, you can:

1. Add API key requirement in API Gateway
2. Add AWS IAM authentication
3. Add custom authorizer Lambda

### Data Availability

The API serves reflections from `quote_history.json` in S3:
- **Today's reflection**: Available after 6 AM PST (when daily job runs)
- **Historical reflections**: Up to 400 days back
- **Future dates**: Will return 404 (not found)

## Troubleshooting

### API Returns 404 for Today

- Check that the daily Lambda ran today at 6 AM PST
- Verify quote_history.json in S3 has today's entry:
  ```bash
  aws s3 cp s3://YOUR_BUCKET_NAME/quote_history.json - | jq '.quotes[-1]'
  ```

### API Gateway 403 Forbidden

- Check API Gateway logs in CloudWatch
- Verify CORS headers are configured
- Ensure Lambda has permission to read S3

### Lambda Execution Errors

View logs:
```bash
aws logs tail /aws/lambda/ReflectionApiHandler --follow
```

Common issues:
- Missing quote_history.json in S3
- Invalid date format in request
- S3 permissions not granted

## Updating the API

To update the API Lambda code in the future:

```bash
# 1. Make changes to lambda/api_handler.py

# 2. Rebuild Lambda package
./build_lambda.sh

# 3. Redeploy
cdk deploy
```

## Documentation

For API usage documentation, see:
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Original deployment guide

## Hardware Device Integration

Once deployed, configure your hardware device with:

1. **API Base URL**: The value from `ApiUrl` output
2. **Endpoint**: `/reflection/today`
3. **Method**: `GET`
4. **Response format**: JSON
5. **Refresh frequency**: Once per day (after 6 AM PST)

Example Python code for hardware device:

```python
import requests

API_URL = "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod"

def get_daily_reflection():
    response = requests.get(f"{API_URL}/reflection/today")
    response.raise_for_status()
    return response.json()

# Fetch and display
reflection = get_daily_reflection()
print(f"{reflection['quote']}\n- {reflection['attribution']}")
print(f"\n{reflection['reflection']}")
```

---

**Questions or issues?** Check CloudWatch Logs or refer to the troubleshooting section above.
