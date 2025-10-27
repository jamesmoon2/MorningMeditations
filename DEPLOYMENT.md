# Deployment Guide - Daily Stoic Reflection Service

Complete step-by-step guide for deploying the Daily Stoic Reflection email service to AWS.

## Prerequisites

### Required Software

- **Python 3.12+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: Required for AWS CDK CLI ([Download Node.js](https://nodejs.org/))
- **AWS CLI**: [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Git**: For version control

### Required Accounts

- **AWS Account**: With administrative access
- **Anthropic Account**: For Claude API access ([Sign up](https://console.anthropic.com/))
- **Domain**: jamescmooney.com (or your own domain) configured in Route 53

### Required Credentials

- AWS Access Key ID and Secret Access Key
- Anthropic API Key

## Step 1: Project Setup (10 minutes)

### Clone or Navigate to Project

```bash
cd /path/to/MorningMeditations
```

### Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install AWS CDK globally (if not already installed)
npm install -g aws-cdk

# Verify CDK installation
cdk --version
```

## Step 2: Configure AWS CLI (5 minutes)

### Set Up AWS Credentials

```bash
aws configure
```

When prompted, enter:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region name**: `us-west-2`
- **Default output format**: `json`

### Verify AWS Connection

```bash
# Check that AWS CLI is configured
aws sts get-caller-identity

# Note your account ID from the output
```

## Step 3: Configure API Keys (5 minutes)

### Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

### Update cdk.json

Edit `cdk.json` and replace the placeholder API key:

```json
{
  "context": {
    "anthropic_api_key": "sk-ant-YOUR-ACTUAL-API-KEY-HERE",
    "sender_email": "reflections@jamescmooney.com",
    "sender_domain": "jamescmooney.com",
    "initial_recipient": "jamesmoon2@gmail.com"
  }
}
```

**Security Note**: For production, consider using AWS Secrets Manager instead of storing the API key in cdk.json.

## Step 4: Set Up Amazon SES (30 minutes)

### 4.1 Verify Domain Identity

```bash
# Verify your domain
aws ses verify-domain-identity \
  --domain jamescmooney.com \
  --region us-west-2

# Enable DKIM signing
aws ses verify-domain-dkim \
  --domain jamescmooney.com \
  --region us-west-2
```

The second command will return 3 DKIM tokens.

### 4.2 Get DNS Records

```bash
# Get domain verification token
aws ses get-identity-verification-attributes \
  --identities jamescmooney.com \
  --region us-west-2

# Get DKIM tokens
aws ses get-identity-dkim-attributes \
  --identities jamescmooney.com \
  --region us-west-2
```

### 4.3 Add DNS Records to Route 53

You need to add these DNS records:

1. **Domain Verification**: TXT record
   - Name: `_amazonses.jamescmooney.com`
   - Value: The verification token from above

2. **DKIM Records**: 3 CNAME records
   - Name: `{token1}._domainkey.jamescmooney.com`
   - Value: `{token1}.dkim.amazonses.com`
   - Repeat for all 3 tokens

**Via AWS Console**:
1. Go to Route 53 → Hosted Zones
2. Click on your domain
3. Create records as specified above

**Via CLI** (example for verification record):
```bash
# Get your hosted zone ID
aws route53 list-hosted-zones-by-name --dns-name jamescmooney.com

# Add TXT record (adjust values)
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch file://dns-changes.json
```

### 4.4 Wait for Verification

DNS propagation can take 5-10 minutes. Check status:

```bash
# Check verification status (repeat until "Success")
aws ses get-identity-verification-attributes \
  --identities jamescmooney.com \
  --region us-west-2
```

### 4.5 Verify Initial Recipient Email (Sandbox Mode)

While in SES sandbox mode, you must verify recipient email addresses:

```bash
aws ses verify-email-identity \
  --email-address jamesmoon2@gmail.com \
  --region us-west-2
```

Check your email inbox and click the verification link.

### 4.6 Test SES Setup

```bash
aws ses send-email \
  --from reflections@jamescmooney.com \
  --destination "ToAddresses=jamesmoon2@gmail.com" \
  --message "Subject={Data='SES Test'},Body={Text={Data='Test email from SES'}}" \
  --region us-west-2
```

If successful, you should receive the test email within 1-2 minutes.

## Step 5: Bootstrap CDK (First Time Only) (5 minutes)

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Bootstrap CDK in your account/region
cdk bootstrap aws://$ACCOUNT_ID/us-west-2
```

This creates necessary S3 buckets and IAM roles for CDK deployments.

## Step 6: Deploy Infrastructure (10 minutes)

### Synthesize CloudFormation Template

```bash
# Generate CloudFormation template
cdk synth
```

This validates your CDK code and generates the CloudFormation template in `cdk.out/`.

### Deploy the Stack

```bash
# Deploy to AWS
cdk deploy

# When prompted, review changes and type 'y' to approve
```

The deployment will:
- Create S3 bucket for state management
- Create Lambda function
- Create EventBridge rule
- Set up IAM roles and permissions
- Output resource names

**Save the outputs** - you'll need them for the next steps:
- BucketName
- LambdaFunctionName
- LambdaFunctionArn

### Verify Deployment

```bash
# Check Lambda function
aws lambda get-function \
  --function-name DailyStoicSender \
  --region us-west-2

# Check EventBridge rule
aws events describe-rule \
  --name DailyStoicTrigger \
  --region us-west-2

# Check S3 bucket (use the bucket name from CDK output)
aws s3 ls | grep daily-stoic
```

## Step 7: Upload Configuration Files (5 minutes)

### Get Bucket Name from CDK Output

```bash
# If you didn't save it, get it from CloudFormation
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name DailyStoicStack \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
  --output text)

echo "Bucket name: $BUCKET_NAME"
```

### Upload Config Files

```bash
# Upload 365-day quotes database
aws s3 cp config/stoic_quotes_365_days.json s3://$BUCKET_NAME/config/stoic_quotes_365_days.json

# Upload quote history (empty initially or from backup)
aws s3 cp config/quote_history.json s3://$BUCKET_NAME/quote_history.json

# Upload recipients list
aws s3 cp config/recipients.json s3://$BUCKET_NAME/recipients.json

# Verify upload
aws s3 ls s3://$BUCKET_NAME/ --recursive
```

## Step 8: Test the Lambda Function (10 minutes)

### Manual Test Invocation

```bash
# Invoke the Lambda function manually
aws lambda invoke \
  --function-name DailyStoicSender \
  --region us-west-2 \
  response.json

# Check the response
cat response.json
```

### Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/DailyStoicSender --follow --region us-west-2
```

### Verify Email Delivery

1. Wait 1-2 minutes
2. Check your email inbox (jamesmoon2@gmail.com)
3. If not in inbox, check spam folder
4. Verify HTML formatting looks correct

### Verify History Update

```bash
# Download and check history file
aws s3 cp s3://$BUCKET_NAME/quote_history.json -

# Should show one entry with today's date and quote attribution
```

## Step 9: Verify Schedule (5 minutes)

### Check EventBridge Rule

```bash
aws events describe-rule \
  --name DailyStoicTrigger \
  --region us-west-2
```

Verify:
- **State**: ENABLED
- **ScheduleExpression**: `cron(0 14 * * ? *)`
- **Targets**: Lambda function

### Understanding the Schedule

The cron expression `cron(0 14 * * ? *)` means:
- **14:00 UTC** daily
- Equals **6:00 AM PST** (UTC-8) / **7:00 AM PDT** (UTC-7)

To adjust the time, edit `infra/stoic_stack.py` and change the `hour` parameter, then redeploy with `cdk deploy`.

## Step 10: Request SES Production Access (Optional)

While in sandbox mode, you can only send to verified email addresses. To send to any address:

### Submit Production Access Request

1. Go to [SES Console](https://console.aws.amazon.com/ses/)
2. Click **Account Dashboard**
3. Click **Request production access**
4. Fill out the form:
   - **Use case**: Personal daily newsletter
   - **Expected volume**: 1-10 emails/day
   - **Content description**: Daily philosophical reflections on Stoicism
   - **Bounce/complaint handling**: Describe your manual process
5. Submit and wait 24-48 hours for approval

## Troubleshooting

### Email Not Delivered

1. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/DailyStoicSender --region us-west-2
   ```

2. **Verify SES Domain Status**:
   ```bash
   aws ses get-identity-verification-attributes \
     --identities jamescmooney.com \
     --region us-west-2
   ```

3. **Check SES Sending Statistics**:
   ```bash
   aws ses get-send-statistics --region us-west-2
   ```

4. **Verify Recipient Email** (if in sandbox):
   ```bash
   aws ses list-identities --region us-west-2
   ```

### Lambda Execution Errors

1. **Check environment variables**:
   ```bash
   aws lambda get-function-configuration \
     --function-name DailyStoicSender \
     --region us-west-2
   ```

2. **Verify IAM permissions**:
   - Lambda needs S3 read/write permissions
   - Lambda needs SES send permissions

3. **Check Anthropic API key**:
   - Ensure it's correctly set in cdk.json
   - Verify it's valid in Anthropic Console

### CDK Deployment Fails

1. **Check for existing stack**:
   ```bash
   aws cloudformation describe-stacks --stack-name DailyStoicStack
   ```

2. **Delete and retry** (if needed):
   ```bash
   cdk destroy
   cdk deploy
   ```

3. **Verify CDK bootstrap**:
   ```bash
   aws cloudformation describe-stacks --stack-name CDKToolkit
   ```

## Next Steps

1. **Monitor First Week**: Check that emails arrive daily at 6 AM PT
2. **Review Costs**: Monitor AWS billing dashboard
3. **Add Recipients**: Edit `config/recipients.json` and re-upload to S3
4. **Review Content**: Assess quote quality and reflection length
5. **Request SES Production Access**: To expand beyond verified recipients

## Useful Commands Reference

```bash
# Manual Lambda invocation
aws lambda invoke --function-name DailyStoicSender response.json

# View logs
aws logs tail /aws/lambda/DailyStoicSender --follow

# Download history
aws s3 cp s3://$BUCKET_NAME/quote_history.json ./

# Update recipients
aws s3 cp config/recipients.json s3://$BUCKET_NAME/recipients.json

# Redeploy after code changes
cdk deploy

# Destroy everything (CAUTION!)
cdk destroy
```

## Support Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **CDK Python Reference**: https://docs.aws.amazon.com/cdk/api/v2/python/
- **Anthropic API Docs**: https://docs.anthropic.com/
- **Project Documentation**: See [README.md](README.md) and [prd.md](prd.md)

---

**Deployment Complete!** Your Daily Stoic Reflection service should now be running automatically every morning at 6 AM PT.
