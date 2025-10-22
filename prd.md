# Product Requirements Document: Daily Stoic Reflection Service

**Version:** 1.0  
**Date:** October 21, 2025  
**Author:** James Mooney  
**Status:** Ready for Implementation

-----

## Table of Contents

1. [Executive Summary](#executive-summary)
1. [Product Overview](#product-overview)
1. [Technical Architecture](#technical-architecture)
1. [Detailed Requirements](#detailed-requirements)
1. [Implementation Specifications](#implementation-specifications)
1. [Monthly Themes](#monthly-themes)
1. [Data Schemas](#data-schemas)
1. [Deployment Guide](#deployment-guide)
1. [Testing Strategy](#testing-strategy)
1. [Cost Analysis](#cost-analysis)
1. [Future Enhancements](#future-enhancements)

-----

## 1. Executive Summary

### Purpose

Build an automated service that delivers daily stoic philosophical reflections via email. Each morning, the system will use Claude (Anthropic’s AI) to select a classical stoic quote and write an original reflection, themed by month, ensuring no repeats within a year.

### Success Criteria

- Reliable daily email delivery at 6:00 AM Pacific Time
- Fresh, unique content every day (no quote repeats within 365 days)
- Monthly thematic organization
- Total operational cost under $5/month
- Simple maintenance and easy to extend distribution list

### Key Technical Decisions

- **Infrastructure:** AWS (Lambda, EventBridge, SES, S3)
- **IaC:** AWS CDK with Python
- **AI Model:** Anthropic Claude Sonnet 4.5
- **Email Format:** HTML
- **State Management:** S3 JSON files

-----

## 2. Product Overview

### User Story

*“As a person interested in stoicism, I want to receive a thoughtful daily reflection based on classical stoic texts each morning, so I can start my day with philosophical wisdom and practical guidance.”*

### Core Features

#### Must-Have (v1.0)

1. Daily automated email delivery at 6 AM PT
1. AI-generated reflections using classical stoic quotes
1. Monthly themed content (12 distinct themes)
1. Quote tracking to prevent repeats within 1 year
1. HTML formatted emails for readability
1. Support for multiple email recipients via config file

#### Nice-to-Have (Future)

- User preferences (time, frequency, theme preferences)
- Web interface for managing subscriptions
- Archive of past reflections
- Mobile app notifications

### User Experience Flow

```
6:00 AM PT Daily:
  1. System wakes up via EventBridge trigger
  2. Lambda retrieves quote history from S3
  3. Lambda calls Anthropic API with monthly theme + exclusion list
  4. Claude generates quote + reflection (~300-400 words)
  5. Lambda updates quote history in S3
  6. Lambda sends formatted HTML email via SES
  7. User receives email within 1-2 minutes
```

-----

## 3. Technical Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                              │
│                                                                 │
│  ┌──────────────┐         ┌─────────────────────────────────┐  │
│  │ EventBridge  │ trigger │   Lambda Function (Python 3.12) │  │
│  │ (Cron Rule)  │────────>│   "daily-stoic-sender"          │  │
│  │ Daily 6am PT │         │                                 │  │
│  └──────────────┘         │  - Fetch quote history          │  │
│                          │  - Call Anthropic API           │  │
│                          │  - Generate reflection          │  │
│                          │  - Update history               │  │
│                          │  - Send email                   │  │
│                          └─────────────────────────────────┘  │
│                                   │ │ │                        │
│                    ┌──────────────┘ │ └────────────┐           │
│                    ▼                ▼              ▼           │
│            ┌───────────┐    ┌─────────────┐  ┌──────────┐     │
│            │    S3     │    │  Anthropic  │  │   SES    │     │
│            │  Bucket   │    │     API     │  │          │     │
│            │           │    │  (External) │  │  Domain: │     │
│            │ Files:    │    └─────────────┘  │ jamescmo-│     │
│            │ - history │                     │ oney.com │     │
│            │ - config  │                     └──────────┘     │
│            └───────────┘                           │           │
│                                                    ▼           │
└────────────────────────────────────────────────────│───────────┘
                                                     │
                                              ┌──────▼──────┐
                                              │   Gmail     │
                                              │ jamesmoon2@ │
                                              └─────────────┘
```

### AWS Services Used

|Service            |Purpose                                              |Cost Impact                           |
|-------------------|-----------------------------------------------------|--------------------------------------|
|**Lambda**         |Execute daily reflection generation and email sending|Free tier: 1M requests/month          |
|**EventBridge**    |Schedule daily trigger at 6 AM PT                    |Free tier: 14M events/month           |
|**S3**             |Store quote history and config files                 |~$0.01/month                          |
|**SES**            |Send HTML emails                                     |$0.10 per 1,000 emails (~$0.003/month)|
|**CloudWatch Logs**|Lambda execution logs (optional debugging)           |Free tier: 5GB/month                  |

**Total Estimated Cost:** < $1/month

### Technology Stack

- **Runtime:** Python 3.12
- **IaC:** AWS CDK (Python)
- **AI API:** Anthropic Claude API
- **Dependencies:**
  - `boto3` (AWS SDK) - included in Lambda runtime
  - `anthropic` (Python SDK)
  - `email.mime` (Python standard library)

-----

## 4. Detailed Requirements

### 4.1 Functional Requirements

#### FR-1: Daily Email Delivery

- **ID:** FR-1
- **Priority:** Critical
- **Description:** System must send one email per day at exactly 6:00 AM Pacific Time
- **Acceptance Criteria:**
  - Email sent every day (including weekends)
  - Delivery time: 6:00 AM PT ± 2 minutes
  - Email successfully reaches inbox (not spam)
  - Email includes both quote and reflection

#### FR-2: AI-Generated Content

- **ID:** FR-2
- **Priority:** Critical
- **Description:** Each reflection must be freshly generated using Claude Sonnet 4.5
- **Acceptance Criteria:**
  - Quote selected from classical stoic texts only:
    - Marcus Aurelius (*Meditations*)
    - Epictetus (*Discourses*, *Enchiridion*)
    - Seneca (*Letters*, *Essays*)
    - Musonius Rufus (*Lectures*)
  - Reflection length: 250-450 words (1-2 minute read)
  - Output token limit: 2000 tokens max
  - Natural, conversational tone
  - Practical application to modern life

#### FR-3: Monthly Themes

- **ID:** FR-3
- **Priority:** High
- **Description:** Content must follow monthly thematic organization
- **Acceptance Criteria:**
  - Theme automatically determined by current month
  - All reflections in a month relate to theme
  - Themes defined in code (see Section 6)

#### FR-4: Quote Tracking & No Repeats

- **ID:** FR-4
- **Priority:** High
- **Description:** System must prevent quote repetition within 365 days
- **Acceptance Criteria:**
  - Track quotes by “Author - Work Section” (e.g., “Marcus Aurelius - Meditations 4.3”)
  - Store history in S3 as JSON
  - Rolling 365-day window (quotes from Oct 2024 can repeat Oct 2025)
  - History file updated after each successful send

#### FR-5: Distribution List Management

- **ID:** FR-5
- **Priority:** Medium
- **Description:** Support multiple email recipients via S3 config file
- **Acceptance Criteria:**
  - Config file format: JSON array of email addresses
  - No code changes needed to add/remove recipients
  - All recipients receive identical content
  - Invalid emails logged but don’t block delivery to valid addresses

#### FR-6: HTML Email Formatting

- **ID:** FR-6
- **Priority:** Medium
- **Description:** Emails must be HTML formatted for readability
- **Acceptance Criteria:**
  - Quote clearly distinguished from reflection
  - Attribution included (author, work, section if applicable)
  - Responsive design (readable on mobile)
  - Fallback plain text version included

### 4.2 Non-Functional Requirements

#### NFR-1: Reliability

- Lambda function should complete within 30 seconds (timeout: 60s)
- No manual intervention required for daily operation

#### NFR-2: Cost Efficiency

- Total monthly cost < $5 (excluding Anthropic API)
- Anthropic API cost: ~$0.30-0.50/month (2000 tokens × 30 days × $3/1M tokens)

#### NFR-3: Maintainability

- Infrastructure defined as code (AWS CDK)
- Clear code comments and documentation
- Single command deployment
- Easy to modify themes, prompt, or schedule

#### NFR-4: Security

- Anthropic API key stored in environment variables (not in code)
- SES domain verification required
- S3 bucket not publicly accessible
- Lambda execution role follows least privilege

#### NFR-5: Observability

- CloudWatch logs for debugging
- No alerts/monitoring needed (non-critical service)

-----

## 5. Implementation Specifications

### 5.1 Project Structure

```
daily-stoic-reflection/
├── README.md
├── requirements.txt
├── cdk.json
├── app.py                          # CDK app entry point
├── lambda/
│   ├── handler.py                  # Main Lambda function
│   ├── anthropic_client.py         # Anthropic API wrapper
│   ├── email_formatter.py          # HTML email templates
│   ├── quote_tracker.py            # S3 history management
│   └── requirements.txt            # Lambda dependencies
├── infra/
│   ├── __init__.py
│   └── stoic_stack.py              # CDK stack definition
└── config/
    └── recipients.json             # Email distribution list (uploaded to S3)
```

### 5.2 Lambda Function Handler (`lambda/handler.py`)

#### Pseudocode Flow

```python
def lambda_handler(event, context):
    """
    Main Lambda function triggered daily by EventBridge
    """
    # 1. Initialize
    current_date = get_current_date_pt()
    current_month = current_date.month
    theme = get_monthly_theme(current_month)
    
    # 2. Load quote history from S3
    history = load_quote_history_from_s3()
    used_quotes = get_quotes_from_last_365_days(history, current_date)
    
    # 3. Load recipient config from S3
    recipients = load_recipients_from_s3()
    
    # 4. Generate reflection via Anthropic API
    prompt = build_prompt(theme, used_quotes)
    reflection_data = call_anthropic_api(prompt)
    
    # 5. Parse response
    quote = extract_quote(reflection_data)
    attribution = extract_attribution(reflection_data)
    reflection = extract_reflection(reflection_data)
    
    # 6. Update history in S3
    add_to_history(history, current_date, attribution)
    save_quote_history_to_s3(history)
    
    # 7. Format and send email
    html_content = format_html_email(quote, attribution, reflection, theme)
    plain_text = format_plain_text_email(quote, attribution, reflection)
    
    for recipient in recipients:
        send_email_via_ses(recipient, html_content, plain_text)
    
    # 8. Return success
    return {
        'statusCode': 200,
        'body': f'Successfully sent to {len(recipients)} recipients'
    }
```

### 5.3 Anthropic API Integration

#### Prompt Template

```python
def build_prompt(theme: str, used_quotes: list[str]) -> str:
    """
    Build the prompt for Claude to generate a stoic reflection.
    
    Args:
        theme: Monthly theme (e.g., "Discipline and Self-Improvement")
        used_quotes: List of recently used quotes to avoid
    
    Returns:
        Formatted prompt string
    """
    exclusion_list = "\n".join([f"- {quote}" for quote in used_quotes])
    
    prompt = f"""You are a thoughtful teacher of stoic philosophy. Your task is to create a daily reflection for someone interested in applying stoic wisdom to modern life.

Current Month's Theme: {theme}

Requirements:
1. Select ONE quote from classical stoic texts:
   - Marcus Aurelius (Meditations)
   - Epictetus (Discourses or Enchiridion)
   - Seneca (Letters or Essays)
   - Musonius Rufus (Lectures)

2. The quote should relate to this month's theme: {theme}

3. Do NOT use any of these recently used quotes:
{exclusion_list}

4. Write a reflection (250-450 words) that:
   - Explains the quote's meaning
   - Connects it to modern life with a concrete example
   - Offers practical, actionable guidance
   - Uses a warm, conversational tone
   - Avoids academic jargon

5. Format your response as JSON:
{{
  "quote": "The exact quote text",
  "attribution": "Author - Work Section (e.g., 'Marcus Aurelius - Meditations 4.3')",
  "reflection": "Your full reflection text here"
}}

Write the reflection now."""
    
    return prompt
```

#### API Call Specifications

- **Model:** `claude-sonnet-4-5-20250929`
- **Max Tokens:** 2000
- **Temperature:** 1.0 (default, for creativity)
- **System Message:** None (all context in user message)
- **Timeout:** 25 seconds
- **Retry Logic:** None (graceful failure acceptable)

### 5.4 S3 Data Files

#### Quote History File: `s3://daily-stoic-bucket/quote_history.json`

```json
{
  "quotes": [
    {
      "date": "2025-10-21",
      "attribution": "Marcus Aurelius - Meditations 2.1",
      "theme": "Mortality and Impermanence"
    },
    {
      "date": "2025-10-20",
      "attribution": "Epictetus - Enchiridion 1",
      "theme": "Mortality and Impermanence"
    }
  ]
}
```

#### Recipient Config File: `s3://daily-stoic-bucket/recipients.json`

```json
{
  "recipients": [
    "jamesmoon2@gmail.com"
  ]
}
```

### 5.5 Email Template (HTML)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Stoic Reflection</title>
    <style>
        body {
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            color: #2c3e50;
            font-size: 28px;
        }
        .theme {
            color: #7f8c8d;
            font-style: italic;
            font-size: 14px;
            margin-top: 5px;
        }
        .quote {
            font-size: 18px;
            font-style: italic;
            color: #34495e;
            margin: 30px 0;
            padding: 20px;
            background-color: #ecf0f1;
            border-left: 4px solid #3498db;
        }
        .attribution {
            text-align: right;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 10px;
        }
        .reflection {
            margin-top: 30px;
            font-size: 16px;
            text-align: justify;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            font-size: 12px;
            color: #95a5a6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Daily Stoic Reflection</h1>
            <div class="theme">{{ theme }}</div>
        </div>
        
        <div class="quote">
            {{ quote }}
            <div class="attribution">— {{ attribution }}</div>
        </div>
        
        <div class="reflection">
            {{ reflection }}
        </div>
        
        <div class="footer">
            Daily Stoic Reflection • Powered by Claude
        </div>
    </div>
</body>
</html>
```

### 5.6 AWS CDK Stack (`infra/stoic_stack.py`)

#### Stack Components

1. **S3 Bucket**
- Name: `daily-stoic-reflection-{account-id}`
- Versioning: Enabled (for history file safety)
- Encryption: AES256
- Public access: Blocked
- Files: `quote_history.json`, `recipients.json`
1. **Lambda Function**
- Runtime: Python 3.12
- Memory: 256 MB (sufficient for API calls)
- Timeout: 60 seconds
- Environment Variables:
  - `ANTHROPIC_API_KEY` (from CDK context or Secrets Manager)
  - `BUCKET_NAME`
  - `SENDER_EMAIL` = “reflections@jamescmooney.com”
- IAM Role:
  - S3 read/write access to bucket
  - SES send email permissions
  - CloudWatch Logs write
1. **EventBridge Rule**
- Schedule: `cron(0 14 * * ? *)` (6 AM PT = 14:00 UTC, accounting for DST)
- Target: Lambda function
- Note: For PST/PDT handling, we use UTC 14:00 (2 PM UTC) which is:
  - 6 AM PST (Nov-Mar)
  - 7 AM PDT (Mar-Nov)
- **Alternative:** Use `cron(0 13 * * ? *)` for 6 AM PDT / 5 AM PST
- **Recommendation:** Start with 14:00 UTC, adjust seasonally if needed
1. **SES Configuration**
- Domain: jamescmooney.com
- Verified identity
- DKIM signing enabled
- Initially in sandbox mode

#### CDK Code Snippet

```python
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
    aws_ses as ses,
    aws_iam as iam,
    Duration
)

class StoicStack(Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # S3 Bucket for state
        bucket = s3.Bucket(self, "StoicBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )
        
        # Lambda Function
        lambda_fn = lambda_.Function(self, "DailyStoicSender",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(60),
            memory_size=256,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "SENDER_EMAIL": "reflections@jamescmooney.com",
                "ANTHROPIC_API_KEY": self.node.try_get_context("anthropic_api_key")
            }
        )
        
        # Grant permissions
        bucket.grant_read_write(lambda_fn)
        
        lambda_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["ses:SendEmail", "ses:SendRawEmail"],
            resources=["*"]
        ))
        
        # EventBridge Rule (6 AM Pacific)
        rule = events.Rule(self, "DailyTrigger",
            schedule=events.Schedule.cron(
                minute="0",
                hour="14",  # 6 AM PT (accounts for DST)
                month="*",
                day="*",
                year="*"
            )
        )
        
        rule.add_target(targets.LambdaFunction(lambda_fn))
```

-----

## 6. Monthly Themes

Each month has a distinct theme that guides quote selection and reflection content. Themes are defined programmatically:

```python
MONTHLY_THEMES = {
    1: {
        "name": "Discipline and Self-Improvement",
        "description": "Focus on building habits, self-control, and starting fresh"
    },
    2: {
        "name": "Relationships and Community",
        "description": "Our connections to others, love, friendship, and social virtue"
    },
    3: {
        "name": "Resilience and Adversity",
        "description": "Facing challenges, growing through difficulty, and mental toughness"
    },
    4: {
        "name": "Nature and Acceptance",
        "description": "Living in accordance with nature, accepting what is"
    },
    5: {
        "name": "Virtue and Character",
        "description": "The four cardinal virtues (wisdom, justice, courage, temperance)"
    },
    6: {
        "name": "Wisdom and Philosophy",
        "description": "The love of wisdom, continuous learning, and philosophical practice"
    },
    7: {
        "name": "Freedom and Autonomy",
        "description": "Inner freedom, independence of mind, and self-sufficiency"
    },
    8: {
        "name": "Patience and Endurance",
        "description": "Long-term thinking, persistence, and bearing hardship"
    },
    9: {
        "name": "Purpose and Calling",
        "description": "Finding meaning, living deliberately, and fulfilling your role"
    },
    10: {
        "name": "Mortality and Impermanence",
        "description": "Memento mori, making the most of time, and perspective on death"
    },
    11: {
        "name": "Gratitude and Contentment",
        "description": "Appreciating what we have, finding sufficiency, and thanksgiving"
    },
    12: {
        "name": "Reflection and Legacy",
        "description": "Year-end contemplation, examining life, and what we leave behind"
    }
}
```

-----

## 7. Data Schemas

### 7.1 Quote History Schema

**File:** `quote_history.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "quotes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "date": {
            "type": "string",
            "format": "date",
            "description": "ISO 8601 date (YYYY-MM-DD)"
          },
          "attribution": {
            "type": "string",
            "description": "Author - Work Section (e.g., 'Marcus Aurelius - Meditations 4.3')"
          },
          "theme": {
            "type": "string",
            "description": "Monthly theme when this was sent"
          }
        },
        "required": ["date", "attribution", "theme"]
      }
    }
  },
  "required": ["quotes"]
}
```

### 7.2 Recipients Config Schema

**File:** `recipients.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "recipients": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "email",
        "description": "Valid email address"
      },
      "minItems": 1,
      "uniqueItems": true
    }
  },
  "required": ["recipients"]
}
```

### 7.3 Anthropic API Response Schema

**Expected JSON Response from Claude:**

```json
{
  "quote": "String containing the exact stoic quote",
  "attribution": "Author - Work Section",
  "reflection": "Full reflection text (250-450 words)"
}
```

**Parsing Logic:**

```python
def parse_anthropic_response(response_text: str) -> dict:
    """
    Parse Claude's response and extract structured data.
    Handles both JSON and potential markdown formatting.
    """
    # Try to extract JSON from response
    # Handle cases where Claude wraps JSON in markdown code blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = response_text
    
    data = json.loads(json_str)
    
    # Validate required fields
    required = ['quote', 'attribution', 'reflection']
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    return data
```

-----

## 8. Deployment Guide

### 8.1 Prerequisites

**AWS Setup:**

1. AWS Account with administrative access
1. AWS CLI installed and configured
1. AWS CDK CLI installed: `npm install -g aws-cdk`
1. Python 3.12+ installed locally

**Domain Setup:**

1. Domain `jamescmooney.com` in Route 53
1. Access to domain DNS settings

**API Keys:**

1. Anthropic API key (from https://console.anthropic.com/)

### 8.2 Step-by-Step Deployment

#### Phase 1: Initial Setup (30 minutes)

**Step 1: Clone/Create Project**

```bash
mkdir daily-stoic-reflection
cd daily-stoic-reflection

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install CDK and dependencies
pip install aws-cdk-lib constructs boto3 anthropic
```

**Step 2: Initialize CDK Project**

```bash
cdk init app --language python
```

**Step 3: Configure Context**
Edit `cdk.json` to add:

```json
{
  "app": "python3 app.py",
  "context": {
    "anthropic_api_key": "YOUR_API_KEY_HERE",
    "sender_email": "reflections@jamescmooney.com",
    "initial_recipient": "jamesmoon2@gmail.com"
  }
}
```

**Note:** For production, use AWS Secrets Manager instead of storing in cdk.json

#### Phase 2: SES Setup (20 minutes)

**Step 4: Verify Domain in SES**

Option A: Using AWS Console

1. Go to SES Console → Verified Identities
1. Click “Create Identity”
1. Select “Domain”
1. Enter `jamescmooney.com`
1. Enable DKIM signing (recommended)
1. Copy the DNS records provided

Option B: Using AWS CLI

```bash
aws ses verify-domain-identity --domain jamescmooney.com --region us-west-2
aws ses verify-domain-dkim --domain jamescmooney.com --region us-west-2
```

**Step 5: Add DNS Records to Route 53**

1. Go to Route 53 → Hosted Zones → jamescmooney.com
1. Add TXT record for domain verification (provided by SES)
1. Add CNAME records for DKIM (3 records provided by SES)
1. Wait 5-10 minutes for verification

**Step 6: Verify Email Address (Sandbox Mode)**

```bash
aws ses verify-email-identity --email-address jamesmoon2@gmail.com --region us-west-2
```

Check email inbox for verification link and click it.

**Step 7: Request Production Access (Optional - for future expansion)**

To send emails to unverified addresses:

1. Go to SES Console → Account Dashboard
1. Click “Request production access”
1. Fill out form:
- Use case: Personal daily newsletter
- Expected volume: 1-5 emails/day
- Describe content: Philosophical reflections on stoicism
1. Submit and wait 24-48 hours for approval

#### Phase 3: Deploy Infrastructure (15 minutes)

**Step 8: Create Lambda Code**

Create files according to project structure (Section 5.1)

**Step 9: Bootstrap CDK (First-time only)**

```bash
cdk bootstrap aws://ACCOUNT-ID/us-west-2
```

**Step 10: Deploy Stack**

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy to AWS
cdk deploy
```

Confirm deployment when prompted.

**Step 11: Upload Initial Config Files**

Create initial history file:

```bash
cat > quote_history.json << EOF
{
  "quotes": []
}
EOF

aws s3 cp quote_history.json s3://daily-stoic-reflection-ACCOUNT-ID/quote_history.json
```

Create recipients file:

```bash
cat > recipients.json << EOF
{
  "recipients": ["jamesmoon2@gmail.com"]
}
EOF

aws s3 cp recipients.json s3://daily-stoic-reflection-ACCOUNT-ID/recipients.json
```

#### Phase 4: Testing (10 minutes)

**Step 12: Manual Test Invocation**

```bash
aws lambda invoke \
  --function-name DailyStoicSender \
  --payload '{}' \
  --region us-west-2 \
  response.json

cat response.json
```

**Step 13: Check Email**

- Wait 1-2 minutes
- Check jamesmoon2@gmail.com inbox (and spam folder)
- Verify email formatting and content quality

**Step 14: Verify S3 History Update**

```bash
aws s3 cp s3://daily-stoic-reflection-ACCOUNT-ID/quote_history.json -

# Should show one entry with today's quote
```

#### Phase 5: Production Readiness (5 minutes)

**Step 15: Verify EventBridge Schedule**

```bash
aws events describe-rule --name DailyTrigger --region us-west-2

# Verify: ScheduleExpression shows cron(0 14 * * ? *)
```

**Step 16: Enable CloudWatch Logs (Optional)**

Logs are automatically created, but you can set retention:

```bash
aws logs put-retention-policy \
  --log-group-name /aws/lambda/DailyStoicSender \
  --retention-in-days 7 \
  --region us-west-2
```

### 8.3 Configuration Updates

**Adding Recipients:**

```bash
# Edit recipients.json locally
{
  "recipients": [
    "jamesmoon2@gmail.com",
    "newfriend@example.com"
  ]
}

# Upload to S3
aws s3 cp recipients.json s3://daily-stoic-reflection-ACCOUNT-ID/recipients.json

# If in sandbox mode, verify new email first:
aws ses verify-email-identity --email-address newfriend@example.com --region us-west-2
```

**Changing Schedule:**

```bash
# Edit infra/stoic_stack.py, modify cron expression
# Redeploy
cdk deploy
```

**Updating Lambda Code:**

```bash
# Make changes to lambda/*.py files
cdk deploy
```

-----

## 9. Testing Strategy

### 9.1 Unit Tests (Optional but Recommended)

**Test Quote Tracker:**

```python
# tests/test_quote_tracker.py
import unittest
from datetime import datetime, timedelta
from lambda.quote_tracker import filter_quotes_by_date_range

class TestQuoteTracker(unittest.TestCase):
    def test_365_day_filter(self):
        """Test that quotes older than 365 days are excluded"""
        today = datetime.now()
        history = {
            "quotes": [
                {"date": (today - timedelta(days=300)).isoformat()[:10], "attribution": "Test 1"},
                {"date": (today - timedelta(days=400)).isoformat()[:10], "attribution": "Test 2"},
            ]
        }
        
        filtered = filter_quotes_by_date_range(history, today, days=365)
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["attribution"], "Test 1")
```

**Test Email Formatter:**

```python
# tests/test_email_formatter.py
import unittest
from lambda.email_formatter import format_html_email

class TestEmailFormatter(unittest.TestCase):
    def test_html_generation(self):
        """Test HTML email contains all required elements"""
        html = format_html_email(
            quote="Test quote",
            attribution="Marcus Aurelius - Meditations 2.1",
            reflection="Test reflection",
            theme="Test Theme"
        )
        
        self.assertIn("Test quote", html)
        self.assertIn("Marcus Aurelius", html)
        self.assertIn("Test reflection", html)
        self.assertIn("Test Theme", html)
```

### 9.2 Integration Tests

**Test 1: End-to-End Lambda Execution**

```bash
# Invoke with test event
aws lambda invoke \
  --function-name DailyStoicSender \
  --log-type Tail \
  --query 'LogResult' \
  --output text \
  --region us-west-2 \
  response.json | base64 -d

# Check response
cat response.json
```

**Test 2: S3 History Persistence**

```bash
# Before test
BEFORE=$(aws s3 cp s3://daily-stoic-reflection-ACCOUNT-ID/quote_history.json - | jq '.quotes | length')

# Invoke Lambda
aws lambda invoke --function-name DailyStoicSender response.json

# After test (wait 5 seconds)
sleep 5
AFTER=$(aws s3 cp s3://daily-stoic-reflection-ACCOUNT-ID/quote_history.json - | jq '.quotes | length')

# Verify increment
if [ $AFTER -eq $((BEFORE + 1)) ]; then
  echo "✓ History updated correctly"
else
  echo "✗ History not updated"
fi
```

**Test 3: Email Delivery**

- Manually invoke Lambda
- Wait 2 minutes
- Check inbox
- Verify HTML rendering in Gmail
- Check spam folder if not in inbox

### 9.3 Acceptance Testing

**Daily Operation Verification (Week 1):**

- [ ] Day 1: Email received at 6:00 AM PT ± 5 minutes
- [ ] Day 2: New quote (different from Day 1)
- [ ] Day 3: Quote relates to monthly theme
- [ ] Day 4: Reflection is 1-2 minutes to read
- [ ] Day 5: HTML formatting displays correctly
- [ ] Day 6: Attribution format is correct
- [ ] Day 7: S3 history has 7 entries

**Edge Cases:**

- [ ] Test during PST/PDT transition (manually adjust schedule if needed)
- [ ] Test with invalid recipient email (verify graceful handling)
- [ ] Test with Anthropic API timeout (verify Lambda doesn’t crash)

-----

## 10. Cost Analysis

### 10.1 Monthly Cost Breakdown

|Service            |Usage                       |Unit Cost      |Monthly Cost   |
|-------------------|----------------------------|---------------|---------------|
|**Lambda**         |30 invocations × 10s × 256MB|Free tier      |$0.00          |
|**EventBridge**    |30 events/month             |Free tier      |$0.00          |
|**S3 Storage**     |~1 MB                       |$0.023/GB      |$0.00          |
|**S3 Requests**    |60 PUT/GET requests         |$0.005/1000    |$0.00          |
|**SES Emails**     |30 emails                   |$0.10/1000     |$0.003         |
|**CloudWatch Logs**|~50 MB/month                |Free tier (5GB)|$0.00          |
|**Data Transfer**  |Negligible                  |-              |$0.00          |
|**Anthropic API**  |30 days × 2000 tokens output|$3/1M tokens   |$0.18          |
|                   |                            |**Total**      |**$0.18/month**|

### 10.2 Scaling Cost (10 Recipients)

|Service      |1 Recipient|10 Recipients|
|-------------|-----------|-------------|
|Lambda       |$0.00      |$0.00        |
|SES          |$0.003     |$0.03        |
|Anthropic API|$0.18      |$0.18        |
|**Total**    |**$0.18**  |**$0.21**    |

### 10.3 Annual Cost Projection

**Year 1 (Single Recipient):**

- Infrastructure: ~$2.16
- One-time setup costs: $0
- **Total:** $2.16/year

**Year 1 (10 Recipients):**

- Infrastructure: ~$2.52
- **Total:** $2.52/year

**Extremely cost-effective for daily personalized content!**

-----

## 11. Future Enhancements

### 11.1 Phase 2 Features (Optional)

**Multiple Delivery Times:**

- Allow recipients to choose their preferred time
- Store preferences in DynamoDB or S3 config
- Multiple EventBridge rules or single Lambda with scheduling logic

**User Preferences:**

- Frequency selection (daily, weekdays only, weekly)
- Theme preferences (some users may want focus on certain topics)
- Length preferences (short vs. longer reflections)

**Web Interface:**

- Simple static site (S3 + CloudFront) for subscription management
- API Gateway + Lambda for backend
- Unsubscribe link in emails

**Content Archive:**

- Public/private archive of past reflections
- Search functionality
- “Reflection of the week” highlights

**Analytics:**

- Track email open rates (SES + SNS notifications)
- Most popular quotes
- Engagement metrics

### 11.2 Technical Improvements

**Better Error Handling:**

- Retry logic with exponential backoff for Anthropic API
- SNS alerts on repeated failures
- Fallback to pre-generated quotes if API unavailable

**Performance Optimization:**

- Cache frequently accessed S3 files in Lambda /tmp
- Parallel email sending for large recipient lists
- Lazy loading of dependencies

**Security Enhancements:**

- Store Anthropic API key in AWS Secrets Manager
- Enable S3 bucket access logging
- Add Lambda environment variable encryption

**Observability:**

- Custom CloudWatch metrics (emails sent, API latency)
- X-Ray tracing for debugging
- Structured logging (JSON format)

### 11.3 Content Enhancements

**Quote Variety:**

- Add Buddhist or Taoist philosophical texts
- Include contemporary stoic thinkers (Ryan Holiday, Massimo Pigliucci)
- User voting on favorite quotes to influence selection

**Interactive Elements:**

- “Reflection prompts” - questions for journaling
- Weekly challenges based on stoic principles
- Monthly retrospective emails

**Multimedia:**

- Audio version of reflections (Amazon Polly)
- Illustrated quotes (AI-generated images)
- Video reflections (rare, special occasions)

-----

## 12. Appendix

### 12.1 Troubleshooting Guide

**Email Not Delivered:**

1. Check SES sending statistics in console
1. Verify domain verification status
1. Check spam folder
1. Review Lambda CloudWatch logs
1. Verify recipient email in SES (if sandbox mode)

**Wrong Time Delivery:**

1. EventBridge uses UTC time - verify cron expression
1. Account for PST/PDT differences
1. Manually adjust schedule 2x/year if needed

**Repeated Quotes:**

1. Check S3 history file format
1. Verify Lambda successfully updates S3 after sending
1. Review quote tracker logic in CloudWatch logs

**High Anthropic API Costs:**

1. Verify max_tokens set to 2000
1. Check for runaway loops in Lambda
1. Review CloudWatch metrics for invocation count

### 12.2 Maintenance Schedule

**Weekly:**

- [ ] Verify daily emails received successfully

**Monthly:**

- [ ] Review AWS billing for unexpected charges
- [ ] Spot-check quote quality and variety
- [ ] Verify new month’s theme is correct

**Quarterly:**

- [ ] Review CloudWatch logs for errors
- [ ] Update Lambda dependencies if needed
- [ ] Consider adding new recipients

**Annually:**

- [ ] Review full quote history
- [ ] Audit IAM permissions
- [ ] Consider content/feature enhancements

### 12.3 Useful AWS CLI Commands

```bash
# View Lambda logs
aws logs tail /aws/lambda/DailyStoicSender --follow --region us-west-2

# Manually trigger Lambda
aws lambda invoke --function-name DailyStoicSender response.json --region us-west-2

# Download quote history
aws s3 cp s3://daily-stoic-reflection-ACCOUNT-ID/quote_history.json ./

# Update recipients
aws s3 cp recipients.json s3://daily-stoic-reflection-ACCOUNT-ID/recipients.json

# Check SES sending statistics
aws ses get-send-statistics --region us-west-2

# View EventBridge rule
aws events list-rules --region us-west-2
aws events describe-rule --name DailyTrigger --region us-west-2
```

### 12.4 Reference Links

- **AWS CDK Python Reference:** https://docs.aws.amazon.com/cdk/api/v2/python/
- **AWS Lambda Python Runtime:** https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html
- **AWS SES Developer Guide:** https://docs.aws.amazon.com/ses/latest/dg/
- **Anthropic API Documentation:** https://docs.anthropic.com/
- **EventBridge Cron Expressions:** https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cron-expressions.html
- **Stoic Texts Online:**
  - Meditations: https://www.gutenberg.org/ebooks/2680
  - Enchiridion: https://www.gutenberg.org/ebooks/45109
  - Seneca’s Letters: https://www.gutenberg.org/ebooks/3794

-----

## Document History

|Version|Date      |Author      |Changes             |
|-------|----------|------------|--------------------|
|1.0    |2025-10-21|James Mooney|Initial PRD creation|

-----

**END OF PRD**

This document serves as the complete technical specification for implementing the Daily Stoic Reflection service. All requirements, architecture decisions, and implementation details are documented for handoff to Claude Code or another developer.