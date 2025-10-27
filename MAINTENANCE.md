# Maintenance Guide - Daily Stoic Reflection Service

Guide for ongoing maintenance, updates, and troubleshooting of the Daily Stoic Reflection service.

## Table of Contents

1. [Common Maintenance Tasks](#common-maintenance-tasks)
2. [Adding Recipients](#adding-recipients)
3. [Updating Lambda Code](#updating-lambda-code)
4. [Changing Schedule](#changing-schedule)
5. [Monitoring](#monitoring)
6. [Cost Management](#cost-management)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance Schedule](#maintenance-schedule)

---

## Common Maintenance Tasks

### Adding Recipients

To add new email recipients:

1. **Edit local recipients file**:
   ```bash
   # Edit config/recipients.json
   {
     "recipients": [
       "jamesmoon2@gmail.com",
       "newfriend@example.com"
     ]
   }
   ```

2. **If in SES Sandbox mode**, verify the new email first:
   ```bash
   aws ses verify-email-identity \
     --email-address newfriend@example.com \
     --region us-west-2
   ```

   The recipient will receive a verification email. They must click the link.

3. **Upload updated file to S3**:
   ```bash
   BUCKET_NAME=$(aws cloudformation describe-stacks \
     --stack-name DailyStoicStack \
     --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
     --output text)

   aws s3 cp config/recipients.json s3://$BUCKET_NAME/recipients.json
   ```

4. **Test** (optional):
   ```bash
   aws lambda invoke \
     --function-name DailyStoicSender \
     --region us-west-2 \
     response.json

   cat response.json
   ```

**Note**: If you have SES production access, you can skip step 2.

### Removing Recipients

Simply edit `config/recipients.json`, remove the email address, and upload:

```bash
aws s3 cp config/recipients.json s3://$BUCKET_NAME/recipients.json
```

### Managing the Quotes Database

The system uses a pre-drafted 365-day quote database located in `config/stoic_quotes_365_days.json`.

**To update or modify quotes**:

1. **Validate the database**:
   ```bash
   python3 validate_quotes.py
   ```

   This checks that all 365 days are present and properly formatted.

2. **Test quote loading**:
   ```bash
   python3 test_quote_loader.py
   ```

   This tests loading quotes for various dates including leap years.

3. **Upload to S3**:
   ```bash
   aws s3 cp config/stoic_quotes_365_days.json \
     s3://$BUCKET_NAME/config/stoic_quotes_365_days.json
   ```

4. **Test with Lambda**:
   ```bash
   aws lambda invoke \
     --function-name DailyStoicSender \
     --region us-west-2 \
     response.json
   ```

**Database structure**:
- Organized by month (january, february, etc.)
- Each month contains daily entries with: day, theme, quote, attribution
- Must contain exactly 365 days (no Feb 29 - leap years use Feb 28)

---

## Updating Lambda Code

When you make changes to the Lambda function code:

### 1. Make Code Changes

Edit files in the `lambda/` directory:
- `handler.py` - Main logic and orchestration
- `quote_loader.py` - Loads daily quotes from 365-day database
- `anthropic_client.py` - API interactions for reflection generation
- `email_formatter.py` - Email templates
- `quote_tracker.py` - History archival
- `themes.py` - Monthly themes

### 2. Test Locally (Optional)

Run unit tests:
```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest tests/ -v

# Or test specific module
pytest tests/test_email_formatter.py -v
```

### 3. Deploy Updated Code

```bash
# Redeploy the stack (CDK will detect code changes)
cdk deploy
```

CDK automatically packages the `lambda/` directory and deploys it.

### 4. Verify Deployment

```bash
# Manually invoke to test
aws lambda invoke \
  --function-name DailyStoicSender \
  --region us-west-2 \
  response.json

# Check logs
aws logs tail /aws/lambda/DailyStoicSender --follow --region us-west-2
```

---

## Changing Schedule

### Current Schedule

The default schedule is **6:00 AM PST** (14:00 UTC), which is **7:00 AM PDT**.

### Adjust Delivery Time

1. **Edit `infra/stoic_stack.py`**:
   ```python
   schedule=events.Schedule.cron(
       minute="0",
       hour="13",  # Change this (13 = 6 AM PDT / 5 AM PST)
       month="*",
       week_day="*",
       year="*"
   )
   ```

2. **UTC Time Conversion**:
   - PST (Nov-Mar): UTC = PST + 8
   - PDT (Mar-Nov): UTC = PDT + 7

   Examples:
   - 6 AM PST = 14:00 UTC
   - 6 AM PDT = 13:00 UTC
   - 7 AM PST = 15:00 UTC

3. **Redeploy**:
   ```bash
   cdk deploy
   ```

4. **Verify**:
   ```bash
   aws events describe-rule --name DailyStoicTrigger --region us-west-2
   ```

### Change to Weekdays Only

Edit `infra/stoic_stack.py`:
```python
schedule=events.Schedule.cron(
    minute="0",
    hour="14",
    month="*",
    week_day="MON-FRI",  # Monday through Friday only
    year="*"
)
```

Then redeploy with `cdk deploy`.

---

## Monitoring

### Check Daily Execution

#### View Recent Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/DailyStoicSender --follow --region us-west-2

# View logs from last 24 hours
aws logs tail /aws/lambda/DailyStoicSender --since 24h --region us-west-2

# Filter for errors only
aws logs tail /aws/lambda/DailyStoicSender --filter-pattern "ERROR" --since 7d
```

#### Check Lambda Metrics

```bash
# Via AWS Console
# Go to Lambda → DailyStoicSender → Monitor tab
# View: Invocations, Duration, Errors, Throttles
```

#### Check SES Metrics

```bash
# Get sending statistics
aws ses get-send-statistics --region us-west-2

# Check bounce/complaint rate (should be near 0)
```

### Verify Quote History

```bash
# Download history file
aws s3 cp s3://$BUCKET_NAME/quote_history.json ./

# View recent quotes
cat quote_history.json | jq '.quotes | .[-10:]'

# Count total quotes
cat quote_history.json | jq '.quotes | length'
```

---

## Cost Management

### Monitor AWS Costs

#### Via AWS Console

1. Go to **AWS Billing Dashboard**
2. Check **Cost Explorer**
3. Filter by service:
   - Lambda
   - S3
   - EventBridge
   - SES

#### Expected Monthly Costs

| Service | Expected Cost |
|---------|--------------|
| Lambda | $0.00 (free tier) |
| EventBridge | $0.00 (free tier) |
| S3 | $0.01 |
| SES | $0.003 (1 recipient) - $0.03 (10 recipients) |
| CloudWatch Logs | $0.00 (free tier) |
| **Total** | **< $0.05/month** |

**Plus Anthropic API**: ~$0.18/month (30 days × 2000 tokens × $3/1M tokens)

### Check Anthropic Usage

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. View **Usage** tab
3. Monitor token consumption

Expected: ~2000 tokens/day = 60,000 tokens/month

### Set Up Billing Alerts

```bash
# Create SNS topic for alerts
aws sns create-topic --name billing-alerts --region us-east-1

# Subscribe your email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:billing-alerts \
  --protocol email \
  --notification-endpoint jamesmoon2@gmail.com

# Create billing alarm (via CloudWatch Console)
# Threshold: $5/month
```

---

## Troubleshooting

### No Email Received

**Step 1: Check Lambda Execution**
```bash
# Check if Lambda ran
aws logs filter-log-events \
  --log-group-name /aws/lambda/DailyStoicSender \
  --start-time $(date -u -d '1 hour ago' +%s000) \
  --region us-west-2
```

**Step 2: Check for Errors**
```bash
aws logs tail /aws/lambda/DailyStoicSender \
  --filter-pattern "ERROR" \
  --since 24h \
  --region us-west-2
```

**Step 3: Verify SES Status**
```bash
# Check domain verification
aws ses get-identity-verification-attributes \
  --identities jamescmooney.com \
  --region us-west-2

# Check if email was sent
aws ses get-send-statistics --region us-west-2
```

**Step 4: Check Spam Folder**

Emails might be filtered. Add `reflections@jamescmooney.com` to contacts.

**Step 5: Manually Test**
```bash
aws lambda invoke \
  --function-name DailyStoicSender \
  --region us-west-2 \
  response.json

cat response.json
```

### Wrong Quote for Date

**Cause**: Quotes database not loaded properly or corrupted.

**Fix**:
```bash
# Verify quotes database exists in S3
aws s3 ls s3://$BUCKET_NAME/config/

# Download and validate locally
aws s3 cp s3://$BUCKET_NAME/config/stoic_quotes_365_days.json ./
python3 validate_quotes.py

# Re-upload if needed
aws s3 cp config/stoic_quotes_365_days.json \
  s3://$BUCKET_NAME/config/stoic_quotes_365_days.json
```

**Note**: The system loads quotes by date (month + day), so each day gets a specific quote from the 365-day database. History tracking is now for archival purposes only.

### Lambda Timeout

**Symptoms**: Logs show timeout after 60 seconds.

**Causes**:
- Anthropic API slow to respond
- Network issues

**Fix**: Increase timeout in `infra/stoic_stack.py`:
```python
timeout=Duration.seconds(90)  # Increase from 60 to 90
```

Then redeploy: `cdk deploy`

### High Anthropic API Costs

**Check Usage**:
```bash
# Review logs for API calls
aws logs tail /aws/lambda/DailyStoicSender \
  --filter-pattern "Anthropic API" \
  --since 7d
```

**Verify**:
- Only 1 invocation per day
- Max tokens set to 2000
- No runaway loops

### Wrong Delivery Time

**Verify Schedule**:
```bash
aws events describe-rule --name DailyStoicTrigger --region us-west-2
```

**Remember**:
- EventBridge uses UTC time
- PST = UTC - 8 hours
- PDT = UTC - 7 hours
- Daylight Saving Time changes twice a year

**Solution**: Adjust cron expression in `infra/stoic_stack.py` and redeploy.

---

## Maintenance Schedule

### Daily (Automated)

- ✅ Lambda runs at 6 AM PT
- ✅ Email sent to recipients
- ✅ Quote history updated

### Weekly

Manual checks:

- [ ] Verify emails received all 7 days
- [ ] Check spam folder if missing
- [ ] Review CloudWatch logs for errors

```bash
# Quick check command
aws logs filter-log-events \
  --log-group-name /aws/lambda/DailyStoicSender \
  --start-time $(date -u -d '7 days ago' +%s000) \
  --filter-pattern "ERROR"
```

### Monthly

- [ ] Review AWS billing
- [ ] Check Anthropic API usage
- [ ] Verify monthly theme is correct
- [ ] Review quote variety
- [ ] Check S3 storage size

```bash
# Check S3 bucket size
aws s3 ls s3://$BUCKET_NAME --recursive --human-readable --summarize

# Review theme for current month
python3 -c "from lambda.themes import get_monthly_theme; import datetime; print(get_monthly_theme(datetime.datetime.now().month))"
```

### Quarterly

- [ ] Review CloudWatch logs for patterns
- [ ] Update Lambda dependencies if needed
- [ ] Consider adding new recipients
- [ ] Review and refine prompts (if needed)
- [ ] Run full test suite

```bash
# Update dependencies
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt

# Run tests
pytest tests/ -v

# Redeploy
cdk deploy
```

### Annually

- [ ] Review full year of quotes
- [ ] Audit IAM permissions
- [ ] Review all 12 monthly themes
- [ ] Consider feature enhancements
- [ ] Clean up old CloudWatch logs
- [ ] Archive quote history

```bash
# Download full history
aws s3 cp s3://$BUCKET_NAME/quote_history.json ./quote_history_backup_$(date +%Y%m%d).json

# Count quotes by theme
cat quote_history.json | jq '[.quotes[].theme] | group_by(.) | map({theme: .[0], count: length})'
```

---

## Backup and Recovery

### Backup Quote History

```bash
# Download and backup locally
aws s3 cp s3://$BUCKET_NAME/quote_history.json \
  ./backups/quote_history_$(date +%Y%m%d).json

# Or sync to another S3 bucket
aws s3 sync s3://$BUCKET_NAME s3://backup-bucket/daily-stoic/
```

### Restore from Backup

```bash
# Upload backup to S3
aws s3 cp ./backups/quote_history_20251022.json \
  s3://$BUCKET_NAME/quote_history.json
```

### Disaster Recovery

If the stack is accidentally deleted:

1. **Restore from Git**:
   ```bash
   git clone <repository-url>
   cd MorningMeditations
   ```

2. **Restore Configuration**:
   - Update `cdk.json` with API key
   - Verify `config/recipients.json`

3. **Redeploy**:
   ```bash
   source .venv/bin/activate
   cdk deploy
   ```

4. **Restore Data**:
   ```bash
   aws s3 cp ./backups/quote_history_latest.json s3://$BUCKET_NAME/quote_history.json
   aws s3 cp config/recipients.json s3://$BUCKET_NAME/recipients.json
   ```

---

## Useful Commands Cheat Sheet

```bash
# Environment setup
export BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name DailyStoicStack \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
  --output text)

# Manual trigger
aws lambda invoke --function-name DailyStoicSender response.json

# View recent logs
aws logs tail /aws/lambda/DailyStoicSender --follow

# Download history
aws s3 cp s3://$BUCKET_NAME/quote_history.json ./

# Upload recipients
aws s3 cp config/recipients.json s3://$BUCKET_NAME/

# Redeploy after changes
cdk deploy

# Run tests
pytest tests/ -v

# Check costs
aws ce get-cost-and-usage --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity MONTHLY --metrics BlendedCost
```

---

## Getting Help

- **AWS Support**: https://console.aws.amazon.com/support/
- **Anthropic Support**: support@anthropic.com
- **Project Documentation**: [README.md](README.md), [prd.md](prd.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Last Updated**: October 27, 2025
**Changes**: Updated for simplified quote system using pre-drafted 365-day database
