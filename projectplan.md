# Daily Stoic Reflection Service - Implementation Project Plan

> **⚠️ DEPRECATION NOTICE**: This project plan describes the original implementation with AI-generated quotes. The system was simplified on October 27, 2025 to use pre-drafted quotes. This document is kept for historical reference. See [ARCHITECTURE.md](ARCHITECTURE.md) and [DEPLOYMENT.md](DEPLOYMENT.md) for current system documentation.

**Project:** Daily Stoic Reflection Email Service
**Timeline:** 6-8 hours total implementation time
**Developer:** Pair programming with Claude Code
**Date:** October 21, 2025
**Status:** DEPRECATED - Original implementation plan

-----

## Project Overview

Build an automated daily stoic reflection email service using AWS infrastructure, Claude AI, and Python. The system will send personalized philosophical reflections every morning at 6 AM PT.

**Key Deliverables:**

1. Functioning AWS infrastructure (Lambda, EventBridge, SES, S3)
1. Python Lambda function with Anthropic API integration
1. Infrastructure as Code using AWS CDK
1. Complete testing and deployment
1. Documentation and maintenance guides

-----

## Implementation Phases Summary

|Phase    |Description                   |Time Estimate      |
|---------|------------------------------|-------------------|
|**1**    |Project Setup & Environment   |45 minutes         |
|**2**    |AWS Infrastructure Setup      |60 minutes         |
|**3**    |Lambda Function Implementation|120 minutes        |
|**4**    |Testing & Debugging           |45 minutes         |
|**5**    |Deployment & Verification     |30 minutes         |
|**6**    |Documentation                 |30 minutes         |
|**Total**|                              |**5.5 - 6.5 hours**|

-----

## Phase 1: Project Setup & Environment (45 minutes)

### Task 1.1: Initialize Project Structure (15 min)

**Objective:** Create project directory structure and version control

**Steps:**

```bash
mkdir daily-stoic-reflection
cd daily-stoic-reflection
git init
```

**Create Directory Structure:**

```
daily-stoic-reflection/
├── README.md
├── .gitignore
├── requirements.txt
├── cdk.json
├── app.py
├── lambda/
│   ├── __init__.py
│   ├── handler.py
│   ├── anthropic_client.py
│   ├── email_formatter.py
│   ├── quote_tracker.py
│   ├── themes.py
│   └── requirements.txt
├── infra/
│   ├── __init__.py
│   └── stoic_stack.py
├── config/
│   ├── recipients.json
│   └── quote_history.json
└── tests/
    ├── __init__.py
    ├── test_quote_tracker.py
    └── test_email_formatter.py
```

**Files to Create:**

`.gitignore`:

```
.venv/
__pycache__/
*.pyc
*.egg-info/
.pytest_cache/
cdk.out/
.DS_Store
*.swp
cdk.context.json
response.json
```

`README.md`:

```markdown
# Daily Stoic Reflection Email Service

Automated daily stoic philosophy reflections delivered via email using AWS and Claude AI.

## Setup
See DEPLOYMENT.md for complete setup instructions.

## Quick Start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk deploy
```

```
**Success Criteria:**
- [ ] Directory structure created
- [ ] Git repository initialized
- [ ] .gitignore properly configured
- [ ] README.md created

---

### Task 1.2: Set Up Python Virtual Environment (10 min)
**Objective:** Create isolated Python environment with dependencies

**Steps:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project dependencies
pip install --upgrade pip
pip install boto3 anthropic pytest

# Install CDK
pip install aws-cdk-lib constructs

# Freeze dependencies
pip freeze > requirements.txt
```

**Create `lambda/requirements.txt`:**

```
anthropic>=0.18.0
```

**Success Criteria:**

- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] requirements.txt generated
- [ ] lambda/requirements.txt created

-----

### Task 1.3: Configure AWS & CDK (20 min)

**Objective:** Set up AWS credentials and initialize CDK project

**Steps:**

1. **Configure AWS CLI:**

```bash
aws configure
# Enter AWS Access Key ID
# Enter AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

1. **Bootstrap CDK (if not already done):**

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Bootstrap CDK
cdk bootstrap aws://$ACCOUNT_ID/us-east-1
```

1. **Create cdk.json:**

```json
{
  "app": "python3 app.py",
  "watch": {
    "include": [
      "**"
    ],
    "exclude": [
      "README.md",
      "cdk*.json",
      "**/*.pyc",
      ".git/**",
      ".venv/**"
    ]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target-partitions": ["aws"],
    "aws-cdk:enableDiffNoFail": "true",
    "@aws-cdk/core:stackRelativeExports": "true",
    "anthropic_api_key": "sk-ant-REPLACE_WITH_YOUR_KEY",
    "sender_email": "reflections@jamescmooney.com",
    "sender_domain": "jamescmooney.com",
    "initial_recipient": "jamesmoon2@gmail.com"
  }
}
```

1. **Test AWS Connection:**

```bash
aws sts get-caller-identity
```

**Success Criteria:**

- [ ] AWS CLI configured
- [ ] CDK bootstrapped
- [ ] cdk.json created with proper context
- [ ] AWS connection verified

-----

## Phase 2: AWS Infrastructure Setup (60 minutes)

### Task 2.1: Set Up Amazon SES (30 min)

**Objective:** Configure email sending infrastructure

**Steps:**

1. **Verify Domain Identity:**

```bash
aws ses verify-domain-identity \
  --domain jamescmooney.com \
  --region us-east-1
```

1. **Enable DKIM:**

```bash
aws ses verify-domain-dkim \
  --domain jamescmooney.com \
  --region us-east-1
```

This will return 3 DKIM tokens to add as CNAME records.

1. **Get DNS Records:**

```bash
# Get verification token
aws ses get-identity-verification-attributes \
  --identities jamescmooney.com \
  --region us-east-1

# Get DKIM tokens
aws ses get-identity-dkim-attributes \
  --identities jamescmooney.com \
  --region us-east-1
```

1. **Add DNS Records to Route 53:**

Via AWS Console:

- Go to Route 53 → Hosted Zones → jamescmooney.com
- Add TXT record: `_amazonses.jamescmooney.com` with verification token
- Add 3 CNAME records for DKIM (format: `token._domainkey.jamescmooney.com`)

Or via CLI:

```bash
# Create change batch JSON file first, then:
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch file://dns-records.json
```

1. **Wait for Verification (5-10 minutes):**

```bash
# Check status (repeat until verified)
aws ses get-identity-verification-attributes \
  --identities jamescmooney.com \
  --region us-east-1
```

1. **Verify Recipient Email (Sandbox Mode):**

```bash
aws ses verify-email-identity \
  --email-address jamesmoon2@gmail.com \
  --region us-east-1
```

Check inbox for verification email and click the link.

1. **Test SES Setup:**

```bash
aws ses send-email \
  --from reflections@jamescmooney.com \
  --destination "ToAddresses=jamesmoon2@gmail.com" \
  --message "Subject={Data='Test Email'},Body={Text={Data='This is a test from SES'}}" \
  --region us-east-1
```

**Success Criteria:**

- [ ] Domain verified in SES
- [ ] DKIM enabled (all 3 tokens verified)
- [ ] DNS records added to Route 53
- [ ] Recipient email verified
- [ ] Test email received successfully

**Troubleshooting:**

- If verification takes > 10 minutes, check DNS propagation: `dig TXT _amazonses.jamescmooney.com`
- If emails not received, check spam folder
- For DKIM issues: `dig CNAME token._domainkey.jamescmooney.com`

-----

### Task 2.2: Write CDK Stack Code (30 min)

**Objective:** Define all AWS infrastructure as code

**File: `app.py`**

```python
#!/usr/bin/env python3
import aws_cdk as cdk
from infra.stoic_stack import StoicStack

app = cdk.App()

StoicStack(
    app, 
    "DailyStoicStack",
    env=cdk.Environment(
        region="us-east-1"
    ),
    description="Daily Stoic reflection email service"
)

app.synth()
```

**File: `infra/__init__.py`**

```python
# Empty file to make this a package
```

**File: `infra/stoic_stack.py`** (see full code in deliverables section)

Key components to implement:

1. S3 Bucket for state
1. Lambda Function with proper IAM role
1. EventBridge Rule for daily scheduling
1. Outputs for bucket and function names

**Test CDK Synthesis:**

```bash
cdk synth
```

This should generate CloudFormation template without errors.

**Success Criteria:**

- [ ] app.py created
- [ ] stoic_stack.py implemented with all resources
- [ ] Code compiles: `cdk synth` succeeds
- [ ] CloudFormation template generated in `cdk.out/`

-----

## Phase 3: Lambda Function Implementation (120 minutes)

### Task 3.1: Implement Helper Modules (45 min)

#### Subtask 3.1a: Monthly Themes (10 min)

**File: `lambda/themes.py`**

Implement `MONTHLY_THEMES` dictionary and `get_monthly_theme(month)` function.

**Test:**

```python
from themes import get_monthly_theme
assert get_monthly_theme(1)["name"] == "Discipline and Self-Improvement"
assert get_monthly_theme(10)["name"] == "Mortality and Impermanence"
```

#### Subtask 3.1b: Quote Tracker (20 min)

**File: `lambda/quote_tracker.py`**

Implement `QuoteTracker` class with methods:

- `load_history()` - Load from S3
- `save_history(history)` - Save to S3
- `get_used_quotes(days=365)` - Get quotes from last N days
- `add_quote(date, attribution, theme)` - Add new quote to history

**Test locally:**

```python
# Mock S3 or test with real bucket
tracker = QuoteTracker("test-bucket")
history = tracker.load_history()
used = tracker.get_used_quotes(days=365)
```

#### Subtask 3.1c: Email Formatter (15 min)

**File: `lambda/email_formatter.py`**

Implement functions:

- `format_html_email(quote, attribution, reflection, theme)` - Returns HTML string
- `format_plain_text_email(quote, attribution, reflection)` - Returns plain text

HTML template should match design in PRD.

**Test:**

```python
html = format_html_email(
    "Test quote",
    "Marcus Aurelius - Meditations 2.1",
    "Test reflection",
    "Test Theme"
)
assert "Test quote" in html
assert "Marcus Aurelius" in html
```

**Success Criteria:**

- [ ] themes.py implemented and tested
- [ ] quote_tracker.py implemented and tested
- [ ] email_formatter.py implemented and tested
- [ ] All helper modules have no syntax errors

-----

### Task 3.2: Implement Anthropic Client (30 min)

**File: `lambda/anthropic_client.py`**

**Key Functions:**

1. `build_prompt(theme, used_quotes)` - Creates the prompt for Claude
1. `call_anthropic_api(prompt, api_key)` - Makes API call
1. `parse_response(response)` - Extracts quote, attribution, reflection

**Implementation Notes:**

- Use `anthropic` Python SDK
- Set `max_tokens=2000`
- Model: `claude-sonnet-4-5-20250929`
- Parse JSON from response (handle markdown code blocks)
- Include error handling for API failures

**Test locally:**

```python
from anthropic_client import call_anthropic_api, build_prompt

api_key = "YOUR_KEY"
theme = "Discipline and Self-Improvement"
used_quotes = ["Marcus Aurelius - Meditations 2.1"]

prompt = build_prompt(theme, used_quotes)
result = call_anthropic_api(prompt, api_key)

print(result["quote"])
print(result["attribution"])
print(result["reflection"])
```

**Success Criteria:**

- [ ] build_prompt() generates correct format
- [ ] call_anthropic_api() successfully calls API
- [ ] parse_response() handles JSON and markdown
- [ ] Error handling implemented
- [ ] Local test passes with real API key

-----

### Task 3.3: Implement Main Handler (45 min)

**File: `lambda/handler.py`**

**Main Flow:**

```python
def lambda_handler(event, context):
    # 1. Get environment variables
    # 2. Determine current date/month/theme
    # 3. Load quote history
    # 4. Load recipients
    # 5. Generate reflection via Anthropic
    # 6. Update history
    # 7. Send emails
    # 8. Return success
```

**Key Functions:**

- `lambda_handler(event, context)` - Main entry point
- `load_recipients(bucket_name)` - Load from S3
- `send_email(recipient, html, plain_text, subject, sender)` - Use boto3 SES

**Environment Variables:**

- `BUCKET_NAME`
- `SENDER_EMAIL`
- `ANTHROPIC_API_KEY`
- `REGION`

**Error Handling:**

- Catch and log errors
- Don’t crash on single recipient failure
- Log success/failure for debugging

**Logging:**
Use Python `logging` module:

```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
```

**Success Criteria:**

- [ ] handler.py implements complete flow
- [ ] All helper modules imported correctly
- [ ] Environment variables accessed
- [ ] Error handling in place
- [ ] Logging statements added
- [ ] Code has no syntax errors

-----

## Phase 4: Testing & Debugging (45 minutes)

### Task 4.1: Unit Tests (20 min)

**File: `tests/test_quote_tracker.py`**

Test cases:

- Loading empty history
- Adding quotes
- Filtering by date range (365 days)
- Handling missing S3 file

**File: `tests/test_email_formatter.py`**

Test cases:

- HTML generation
- Plain text generation
- Special characters in quotes
- Long reflections

**Run tests:**

```bash
pytest tests/ -v
```

**Success Criteria:**

- [ ] Unit tests written
- [ ] All tests pass
- [ ] Code coverage > 70%

-----

### Task 4.2: Initialize S3 Files (10 min)

**Create Initial Files:**

`config/quote_history.json`:

```json
{
  "quotes": []
}
```

`config/recipients.json`:

```json
{
  "recipients": [
    "jamesmoon2@gmail.com"
  ]
}
```

**Upload to S3:**

```bash
# Get bucket name from CDK output or use default format
BUCKET_NAME="daily-stoic-reflection-$(aws sts get-caller-identity --query Account --output text)"

aws s3 cp config/quote_history.json s3://$BUCKET_NAME/quote_history.json
aws s3 cp config/recipients.json s3://$BUCKET_NAME/recipients.json
```

**Verify upload:**

```bash
aws s3 ls s3://$BUCKET_NAME/
```

**Success Criteria:**

- [ ] Initial JSON files created
- [ ] Files uploaded to S3
- [ ] Files accessible by Lambda (check permissions)

-----

### Task 4.3: Local Lambda Testing (15 min)

**Create test event:**

`test_event.json`:

```json
{}
```

**Test locally (if using SAM) or deploy and test:**

```bash
# Option 1: Test after deployment
aws lambda invoke \
  --function-name DailyStoicSender \
  --payload '{}' \
  --region us-east-1 \
  response.json

cat response.json
```

**Check CloudWatch Logs:**

```bash
aws logs tail /aws/lambda/DailyStoicSender --follow --region us-east-1
```

**Verify:**

- [ ] Lambda executes without errors
- [ ] Anthropic API called successfully
- [ ] S3 history updated
- [ ] Email sent
- [ ] Logs show success

**Debug Common Issues:**

- API key not found → Check environment variables
- S3 access denied → Check IAM role
- SES error → Check domain verification
- Timeout → Increase Lambda timeout

**Success Criteria:**

- [ ] Lambda invocation succeeds
- [ ] Email received in inbox
- [ ] S3 history file updated
- [ ] No errors in CloudWatch Logs

-----

## Phase 5: Deployment & Verification (30 minutes)

### Task 5.1: Deploy Infrastructure (10 min)

**Deploy CDK Stack:**

```bash
cdk deploy
```

Review changes and confirm deployment.

**Note outputs:**

- Bucket name
- Lambda function name
- EventBridge rule name

**Verify deployment:**

```bash
# Check Lambda function
aws lambda get-function --function-name DailyStoicSender --region us-east-1

# Check EventBridge rule
aws events describe-rule --name DailyTrigger --region us-east-1

# Check S3 bucket
aws s3 ls
```

**Success Criteria:**

- [ ] CDK deployment completes successfully
- [ ] All resources created
- [ ] Outputs captured

-----

### Task 5.2: End-to-End Testing (15 min)

**Manual Trigger Test:**

```bash
aws lambda invoke \
  --function-name DailyStoicSender \
  --log-type Tail \
  --query 'LogResult' \
  --output text \
  --region us-east-1 \
  response.json | base64 -d

echo "\n--- Response ---"
cat response.json
```

**Verify Complete Flow:**

1. Check email inbox (wait 1-2 minutes)
1. Verify HTML formatting
1. Check quote and reflection quality
1. Verify S3 history updated

**Check History File:**

```bash
aws s3 cp s3://$BUCKET_NAME/quote_history.json - | jq '.'
```

Should show one entry with today’s date.

**Test Edge Cases:**

- [ ] Invalid recipient handling (add fake email to recipients.json)
- [ ] Long reflections render correctly
- [ ] Special characters in quotes

**Success Criteria:**

- [ ] Email received successfully
- [ ] HTML renders correctly in Gmail
- [ ] Content quality is good
- [ ] History tracking works
- [ ] No errors in logs

-----

### Task 5.3: Schedule Verification (5 min)

**Verify EventBridge Rule:**

```bash
aws events describe-rule --name DailyTrigger --region us-east-1
```

Confirm:

- Schedule expression: `cron(0 14 * * ? *)`
- State: ENABLED
- Target: Lambda function

**Calculate next execution time:**

```python
from datetime import datetime, timezone

# 14:00 UTC = 6:00 AM PST / 7:00 AM PDT
utc_time = datetime.now(timezone.utc).replace(hour=14, minute=0, second=0)
print(f"Next execution (UTC): {utc_time}")

# Convert to your local time
# PST = UTC - 8, PDT = UTC - 7
```

**Success Criteria:**

- [ ] EventBridge rule is enabled
- [ ] Schedule is correct
- [ ] Lambda function is the target
- [ ] Next execution time calculated

-----

## Phase 6: Documentation & Cleanup (30 minutes)

### Task 6.1: Create Documentation (20 min)

**Update README.md** with:

- Project description
- Architecture diagram (text-based)
- Setup instructions
- Usage guide
- Maintenance notes

**Create DEPLOYMENT.md:**

- Complete deployment guide
- Prerequisites
- Step-by-step instructions
- Troubleshooting section

**Create MAINTENANCE.md:**

- How to add recipients
- How to change schedule
- How to update Lambda code
- Cost monitoring
- Monthly checklist

**Success Criteria:**

- [ ] README.md updated
- [ ] DEPLOYMENT.md created
- [ ] MAINTENANCE.md created
- [ ] All documentation is clear and complete

-----

### Task 6.2: Code Cleanup (10 min)

**Final code review:**

- [ ] Remove debug print statements
- [ ] Add docstrings to all functions
- [ ] Add type hints where missing
- [ ] Remove unused imports
- [ ] Format code consistently
- [ ] Add comments for complex logic

**Run linters:**

```bash
# Install tools
pip install black flake8 mypy

# Format code
black lambda/ infra/

# Check style
flake8 lambda/ infra/

# Type checking
mypy lambda/ infra/
```

**Git commit:**

```bash
git add .
git commit -m "Initial implementation of Daily Stoic Reflection service"
git tag v1.0.0
```

**Success Criteria:**

- [ ] Code is clean and well-documented
- [ ] Linters pass (or acceptable warnings only)
- [ ] Git repository is up to date
- [ ] Tagged with version

-----

## Post-Implementation Checklist

### Immediate (Next 24 hours)

- [ ] Verify first automated email delivery at 6 AM PT
- [ ] Check spam folder if email not received
- [ ] Review CloudWatch logs for first automated run
- [ ] Verify quote is different from test runs

### First Week

- [ ] Monitor daily deliveries
- [ ] Track AWS costs in billing dashboard
- [ ] Verify quotes are not repeating
- [ ] Assess reflection quality and length
- [ ] Gather feedback on content

### First Month

- [ ] Review full month of content
- [ ] Verify monthly theme is appropriate
- [ ] Check quote variety across authors
- [ ] Monitor API costs from Anthropic
- [ ] Consider requesting SES production access

-----

## Troubleshooting Guide

### Common Issues

**Email not received:**

1. Check CloudWatch logs for errors
1. Verify SES domain verification status
1. Check spam folder
1. Verify recipient email is verified (if in sandbox)
1. Check SES sending statistics in console

**Wrong delivery time:**

1. Verify EventBridge cron expression
1. Remember UTC vs PT difference
1. Account for DST changes (PST vs PDT)
1. Check Lambda execution logs for timing

**Repeated quotes:**

1. Verify S3 history file is being updated
1. Check Lambda IAM permissions for S3 write
1. Review quote tracker logic
1. Check exclusion list in prompt

**High costs:**

1. Check Lambda invocation count (should be 1/day)
1. Review Anthropic API usage
1. Verify max_tokens limit (should be 2000)
1. Check for unexpected EventBridge triggers

**API failures:**

1. Verify Anthropic API key is valid
1. Check network connectivity from Lambda
1. Review API rate limits
1. Check error messages in CloudWatch

-----

## Future Enhancements Roadmap

### Phase 2 (Optional - Future Work)

**Priority 1: Production SES Access**

- Request production access from AWS
- Update recipients.json with new emails
- No code changes needed

**Priority 2: Multiple Time Zones**

- Add time zone preference to recipients
- Create separate EventBridge rules or single Lambda with scheduling
- Update recipient config schema

**Priority 3: Web Interface**

- Build simple subscription page (S3 + CloudFront)
- API Gateway + Lambda for subscription management
- Add unsubscribe functionality

**Priority 4: Content Archive**

- Store sent emails in S3
- Create searchable archive page
- Add “view past reflections” feature

**Priority 5: Monitoring & Alerts**

- Add SNS alerts for failures
- CloudWatch dashboards
- Weekly summary email

-----

## Deliverables Checklist

Upon completion, you should have:

### Code

- [ ] Complete CDK infrastructure code
- [ ] Lambda function with all modules
- [ ] Unit tests
- [ ] Configuration files

### AWS Resources

- [ ] S3 bucket with state files
- [ ] Lambda function deployed
- [ ] EventBridge rule scheduled
- [ ] SES domain verified
- [ ] IAM roles and policies

### Documentation

- [ ] README.md
- [ ] DEPLOYMENT.md
- [ ] MAINTENANCE.md
- [ ] Inline code documentation

### Verification

- [ ] Successful manual test
- [ ] Email received and formatted correctly
- [ ] Schedule verified for 6 AM PT
- [ ] Costs monitored and within budget

-----

## Contact & Support

**For AWS issues:**

- AWS Support
- AWS Documentation: https://docs.aws.amazon.com/

**For Anthropic API issues:**

- Anthropic Documentation: https://docs.anthropic.com/
- Anthropic Support: support@anthropic.com

**For project questions:**

- Review PRD document
- Check troubleshooting guide
- Review CloudWatch logs

-----

## Project Sign-off

**Project Complete When:**

1. All tasks in Phases 1-6 completed
1. All checklists marked
1. Email successfully delivered at 6 AM PT
1. Documentation complete
1. Code committed to Git

**Expected Outcome:**
A fully functional, automated daily stoic reflection email service that:

- Runs reliably every morning
- Costs less than $5/month
- Delivers high-quality, unique content
- Requires minimal maintenance
- Can be easily extended

-----

**END OF PROJECT PLAN**

This plan provides step-by-step guidance for implementing the Daily Stoic Reflection service. Follow each phase sequentially, using Claude Code as a pair programming partner for implementation assistance.