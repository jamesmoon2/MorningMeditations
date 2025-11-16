# CLAUDE.md - AI Assistant Guide

This document provides comprehensive guidance for AI assistants (like Claude) working with the MorningMeditations codebase. It explains the architecture, development workflows, coding conventions, and key patterns to follow.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Tech Stack](#architecture--tech-stack)
3. [Codebase Structure](#codebase-structure)
4. [Key Modules & Components](#key-modules--components)
5. [Data Flow & Execution](#data-flow--execution)
6. [Development Workflows](#development-workflows)
7. [Coding Conventions](#coding-conventions)
8. [Testing Strategy](#testing-strategy)
9. [Configuration Management](#configuration-management)
10. [Deployment Process](#deployment-process)
11. [Common Tasks](#common-tasks)
12. [Troubleshooting](#troubleshooting)

---

## Project Overview

**MorningMeditations** is a Daily Stoic Reflection Email Service that delivers philosophical wisdom every morning at 6:00 AM Pacific Time.

### What It Does

- Loads a curated quote from a **365-day database** (one unique quote per calendar day)
- Generates an **original reflection** using Claude (Anthropic's AI)
- Applies **monthly themes** (12 distinct themes throughout the year)
- Sends beautifully formatted **HTML emails** via Amazon SES
- Archives all quotes and reflections to **S3 for posterity**

### Key Features

- **Predictable 365-day rotation**: Same date = same quote each year
- **Monthly thematic focus**: January = "Discipline and Self-Improvement", October = "Mortality and Impermanence", etc.
- **Memory-enabled reflections**: Claude receives previous reflections from the current month to provide diverse philosophical angles
- **Cost-effective**: Runs for ~$0.18/month
- **Fully serverless**: No servers to manage

---

## Architecture & Tech Stack

### Technology Stack

- **Language**: Python 3.12
- **Cloud Platform**: AWS
- **Infrastructure as Code**: AWS CDK (Python)
- **Runtime**: AWS Lambda
- **Scheduling**: Amazon EventBridge
- **Storage**: Amazon S3
- **Email**: Amazon SES
- **AI Model**: Anthropic Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

### AWS Services Used

```
EventBridge (Daily 6 AM PT trigger)
    ↓
Lambda (Python 3.12)
    ├── Load quote from S3 (365-day database)
    ├── Generate reflection via Anthropic API
    ├── Archive to S3 (quote_history.json)
    └── Send emails via SES
```

### Architecture Diagram

```
┌─────────────────┐
│  EventBridge    │  Triggers daily at 6 AM PT
│  Rule           │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Lambda Function                        │
│  (DailyStoicSender)                     │
│                                         │
│  1. Get date & monthly theme            │
│  2. Load quote for date                 │◄────┐
│  3. Load recipients config              │     │
│  4. Load quote history (for context)    │     │  S3 Bucket
│  5. Generate reflection via Claude API  │     │  ├── config/stoic_quotes_365_days.json
│  6. Update history in S3                │────►│  ├── quote_history.json
│  7. Send emails via SES                 │     │  └── recipients.json
└─────────────────────────────────────────┘     │
         │                                      │
         ▼
┌─────────────────┐
│  Amazon SES     │  Sends formatted HTML emails
└─────────────────┘
```

---

## Codebase Structure

```
MorningMeditations/
├── lambda/                          # Lambda function code
│   ├── handler.py                   # Main entry point (lambda_handler)
│   ├── quote_loader.py              # Loads daily quotes from 365-day DB
│   ├── anthropic_client.py          # Generates reflections via Claude API
│   ├── email_formatter.py           # HTML/text email formatting
│   ├── quote_tracker.py             # Archives history to S3
│   ├── themes.py                    # Monthly theme definitions
│   └── typing_extensions.py         # Bundled for Lambda compatibility
│
├── infra/                           # AWS CDK infrastructure as code
│   ├── __init__.py
│   └── stoic_stack.py               # CDK stack definition (Lambda, S3, EventBridge, IAM)
│
├── config/                          # Configuration files (uploaded to S3)
│   ├── stoic_quotes_365_days.json   # 365 curated quotes (one per day)
│   ├── recipients.json              # Email recipient list
│   └── quote_history.json           # Historical archive
│
├── tests/                           # Unit tests
│   ├── __init__.py
│   ├── test_themes.py               # Tests for monthly themes
│   ├── test_quote_tracker.py        # Tests for quote archival
│   └── test_email_formatter.py      # Tests for email formatting
│
├── app.py                           # CDK app entry point
├── cdk.json                         # CDK configuration & context values
├── requirements.txt                 # Python dependencies (CDK, boto3, anthropic, pytest)
│
├── validate_quotes.py               # Validates 365-day quote database
├── test_quote_loader.py             # Tests quote loading logic
├── build_lambda.ps1                 # PowerShell script to build Lambda package
│
├── README.md                        # Project overview
├── ARCHITECTURE.md                  # Detailed architecture documentation
├── DEPLOYMENT.md                    # Step-by-step deployment guide
├── MAINTENANCE.md                   # Operations and maintenance guide
├── prd.md                           # Product requirements document
├── projectplan.md                   # Implementation plan
│
└── .gitignore                       # Git ignore patterns (venv, CDK artifacts, Lambda deps)
```

### Important Files to Know

| File | Purpose | When to Modify |
|------|---------|----------------|
| `lambda/handler.py` | Main Lambda entry point | Adding new features, changing execution flow |
| `lambda/anthropic_client.py` | Claude API integration & prompt engineering | Updating prompt, changing AI model, reflection logic |
| `lambda/themes.py` | Monthly theme definitions | Adding/changing monthly themes |
| `infra/stoic_stack.py` | AWS infrastructure definition | Changing AWS resources, permissions, schedule |
| `config/stoic_quotes_365_days.json` | Quote database (365 quotes) | Adding/editing quotes |
| `config/recipients.json` | Email recipient list | Adding/removing recipients |
| `cdk.json` | CDK configuration | Updating API keys, email settings |

---

## Key Modules & Components

### 1. `lambda/handler.py` - Main Lambda Handler

**Purpose**: Entry point for Lambda execution, orchestrates the entire daily workflow.

**Key Function**: `lambda_handler(event, context)`

**Execution Steps**:
1. Get environment variables (bucket name, sender email, API key)
2. Determine current date, month, and theme
3. Load today's quote from 365-day database
4. Load recipient list from S3
5. Load quote history and get current month's reflections
6. Generate reflection via Anthropic API (with previous reflections for context)
7. Update history in S3
8. Format and send emails via SES
9. Return success/failure status

**Key Functions**:
- `lambda_handler()` - Main entry point
- `load_recipients_from_s3()` - Loads recipient list
- `send_email_via_ses()` - Sends individual email via SES

**Error Handling**: Catches all exceptions, logs errors, returns 500 status on failure.

### 2. `lambda/quote_loader.py` - Quote Database Loader

**Purpose**: Loads daily quotes from the 365-day database based on calendar date.

**Key Class**: `QuoteLoader`

**Key Methods**:
- `load_quotes_database()` - Loads full database from S3 (cached)
- `get_quote_for_date(date)` - Gets quote for specific date (handles leap years)
- `validate_database_completeness()` - Validates all 365 days are present

**Important Logic**:
- Maps calendar date (month + day) to specific quote
- Handles February 29 → uses February 28 quote
- Quotes organized by month name (lowercase) in JSON
- Each quote has: `quote`, `attribution`, `theme`, `day`

**Example Quote Entry**:
```json
{
  "day": 1,
  "quote": "You have power over your mind - not outside events.",
  "attribution": "Marcus Aurelius - Meditations 5.1",
  "theme": "Discipline and Self-Improvement"
}
```

### 3. `lambda/anthropic_client.py` - Claude API Client

**Purpose**: Generates daily reflections using Claude API with sophisticated prompt engineering.

**Key Functions**:
- `build_reflection_prompt()` - Constructs prompt with quote, theme, and previous reflections
- `call_anthropic_api()` - Makes API call to Claude
- `parse_reflection_response()` - Parses JSON response from Claude
- `generate_reflection_only()` - High-level function combining all steps

**Prompt Engineering Strategy**:

The prompt includes:
1. **Context Section**: Previous reflections from current month (if any)
2. **Quote & Attribution**: Today's stoic quote
3. **Monthly Theme**: Central organizing principle
4. **Instructions**:
   - Explain quote in accessible language
   - Connect to 2025 challenges (workplace stress, social media anxiety, etc.)
   - Offer practical, actionable guidance
   - Vary philosophical approach when previous reflections exist
   - 150-250 word reflection
   - Warm, conversational tone
5. **Response Format**: JSON with `reflection` field

**API Configuration**:
- Model: `claude-sonnet-4-5-20250929`
- Temperature: `1.0` (creative diversity)
- Max tokens: `2000`
- Timeout: `25 seconds`

**Memory Feature**: Previous reflections from the current month are passed to Claude to ensure:
- Diverse exploration of the monthly theme
- Varied philosophical angles (dichotomy of control, negative visualization, memento mori, etc.)
- Fresh perspectives without repetition

### 4. `lambda/email_formatter.py` - Email Formatting

**Purpose**: Creates beautiful HTML and plain text emails.

**Key Functions**:
- `format_html_email()` - Responsive HTML template with CSS styling
- `format_plain_text_email()` - Plain text fallback
- `create_email_subject()` - Subject line with theme
- `validate_email_content()` - Validates content meets requirements

**HTML Email Design**:
- Responsive layout (max-width: 600px)
- Georgia serif font for readability
- Quote displayed in highlighted box with left border
- Reflection in justified paragraphs
- Footer with attribution

**Content Validation**:
- Quote present and non-empty
- Attribution present and non-empty
- Reflection present and non-empty
- Reflection minimum 150 words
- Reflection maximum 250 words

### 5. `lambda/quote_tracker.py` - Quote History Archival

**Purpose**: Manages quote history in S3 for archival and context.

**Key Class**: `QuoteTracker`

**Key Methods**:
- `load_history()` - Loads history from S3 (creates empty if not exists)
- `save_history()` - Saves history to S3
- `add_quote()` - Adds new quote/reflection entry
- `get_current_month_quotes()` - Filters history for current month/year
- `cleanup_old_quotes()` - Removes quotes older than 400 days

**History Format**:
```json
{
  "quotes": [
    {
      "date": "2025-11-16",
      "quote": "The quote text...",
      "attribution": "Marcus Aurelius - Meditations 5.1",
      "theme": "Gratitude and Contentment",
      "reflection": "Full reflection text..."
    }
  ]
}
```

**Cleanup Strategy**: Keeps 400 days of history (buffer beyond 365-day cycle) to manage file size.

### 6. `lambda/themes.py` - Monthly Themes

**Purpose**: Defines 12 monthly themes for stoic reflections.

**Data Structure**: `MONTHLY_THEMES` dictionary mapping month number (1-12) to theme info.

**Monthly Themes**:
1. January: Discipline and Self-Improvement
2. February: Relationships and Community
3. March: Resilience and Adversity
4. April: Nature and Acceptance
5. May: Virtue and Character
6. June: Wisdom and Philosophy
7. July: Freedom and Autonomy
8. August: Patience and Endurance
9. September: Purpose and Calling
10. October: Mortality and Impermanence
11. November: Gratitude and Contentment
12. December: Reflection and Legacy

**Key Functions**:
- `get_monthly_theme(month)` - Returns theme name and description
- `get_theme_name(month)` - Returns just the theme name
- `get_theme_description(month)` - Returns just the description

### 7. `infra/stoic_stack.py` - CDK Infrastructure

**Purpose**: Defines all AWS infrastructure as code.

**Key Resources**:

1. **S3 Bucket**:
   - Versioned for safety
   - Server-side encryption
   - Public access blocked
   - Retention policy: RETAIN (not deleted with stack)

2. **Lambda Function**:
   - Function name: `DailyStoicSender`
   - Runtime: Python 3.12
   - Timeout: 60 seconds
   - Memory: 256 MB
   - Code: `lambda_linux/` directory (built package)
   - Environment variables: `BUCKET_NAME`, `SENDER_EMAIL`, `ANTHROPIC_API_KEY`
   - Log retention: 1 week

3. **EventBridge Rule**:
   - Schedule: Daily at 14:00 UTC (6 AM PST / 7 AM PDT)
   - Cron: `0 14 * * ? *`
   - Target: Lambda function

4. **IAM Permissions**:
   - Lambda can read/write S3 bucket
   - Lambda can send emails via SES (`ses:SendEmail`, `ses:SendRawEmail`)

**CloudFormation Outputs**:
- Bucket name
- Lambda function name/ARN
- EventBridge rule name

---

## Data Flow & Execution

### Daily Execution Flow

```
1. EventBridge Rule Triggers (6 AM PT)
   └─> Lambda Function Starts

2. Lambda: Load Environment Variables
   └─> BUCKET_NAME, SENDER_EMAIL, ANTHROPIC_API_KEY

3. Lambda: Determine Date & Theme
   └─> current_date = datetime.now()
   └─> theme = get_monthly_theme(current_date.month)

4. Lambda: Load Quote for Date
   └─> QuoteLoader.get_quote_for_date(current_date)
   └─> Loads from s3://bucket/config/stoic_quotes_365_days.json
   └─> Returns: {quote, attribution, theme}

5. Lambda: Load Recipients
   └─> load_recipients_from_s3(bucket_name)
   └─> Loads from s3://bucket/recipients.json
   └─> Returns: ["email1@example.com", "email2@example.com", ...]

6. Lambda: Load Quote History
   └─> QuoteTracker.load_history()
   └─> Loads from s3://bucket/quote_history.json
   └─> QuoteTracker.get_current_month_quotes(history, current_date)
   └─> Returns: [previous reflections from this month]

7. Lambda: Generate Reflection via Claude API
   └─> build_reflection_prompt(quote, attribution, theme, previous_reflections)
   └─> call_anthropic_api(prompt, api_key)
   └─> parse_reflection_response(response_text)
   └─> Returns: reflection text (150-250 words)

8. Lambda: Update History
   └─> history.add_quote(date, quote, attribution, reflection, theme)
   └─> history.cleanup_old_quotes(keep_days=400)
   └─> QuoteTracker.save_history(history)
   └─> Saves to s3://bucket/quote_history.json

9. Lambda: Format Emails
   └─> html_content = format_html_email(quote, attribution, reflection, theme)
   └─> plain_text = format_plain_text_email(quote, attribution, reflection)
   └─> subject = create_email_subject(theme)

10. Lambda: Send Emails via SES
    └─> For each recipient:
        └─> send_email_via_ses(sender, recipient, subject, html_body, text_body)

11. Lambda: Return Success
    └─> Status 200 with success/failure counts
```

### Quote Selection Logic

**How quotes are selected by date**:

1. Extract month name (e.g., "november") and day number (e.g., 16)
2. Load `stoic_quotes_365_days.json` from S3
3. Navigate to month: `quotes_db["november"]`
4. Find quote where `day == 16`
5. Return quote, attribution, and theme

**Leap Year Handling**: February 29 uses February 28's quote.

**Predictability**: The same calendar date always gets the same quote, ensuring a consistent 365-day rotation year after year.

---

## Development Workflows

### Local Development Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd MorningMeditations

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install AWS CDK globally
npm install -g aws-cdk

# 5. Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)
```

### Testing Locally

```bash
# Run all unit tests
pytest

# Run specific test file
pytest tests/test_themes.py

# Run with coverage
pytest --cov=lambda

# Validate quote database
python validate_quotes.py

# Test quote loader
python test_quote_loader.py
```

### Building Lambda Package

**Important**: Lambda dependencies must be bundled separately because Lambda runs on Amazon Linux.

```bash
# Create lambda_linux directory
mkdir -p lambda_linux

# Copy Lambda code
cp -r lambda/* lambda_linux/

# Install dependencies for Amazon Linux (using Docker)
docker run --rm \
  -v "$PWD":/var/task \
  public.ecr.aws/lambda/python:3.12 \
  pip install -r /var/task/lambda/requirements.txt -t /var/task/lambda_linux/

# Alternative: Use build_lambda.ps1 on Windows (PowerShell script)
```

**Lambda Requirements** (`lambda/requirements.txt`):
```
anthropic>=0.18.0
boto3>=1.28.0
```

### CDK Deployment Workflow

```bash
# 1. Update cdk.json with API key
# Edit cdk.json and set "anthropic_api_key" to your actual key

# 2. Bootstrap CDK (first time only)
cdk bootstrap

# 3. Synthesize CloudFormation template (review changes)
cdk synth

# 4. Deploy infrastructure
cdk deploy

# 5. Upload config files to S3
# Get bucket name from deployment output
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name DailyStoicStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

# Upload config files
aws s3 cp config/stoic_quotes_365_days.json s3://$BUCKET_NAME/config/
aws s3 cp config/recipients.json s3://$BUCKET_NAME/
aws s3 cp config/quote_history.json s3://$BUCKET_NAME/
```

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and test
# ... edit code ...
pytest

# 3. Commit changes
git add .
git commit -m "Description of changes"

# 4. Push to remote
git push -u origin feature/your-feature-name

# 5. Create pull request (via GitHub UI)

# 6. After merge, update main
git checkout main
git pull origin main
```

### Updating Lambda Code

```bash
# 1. Edit code in lambda/ directory
# 2. Test locally with pytest
pytest

# 3. Rebuild Lambda package
# (Use Docker or build_lambda.ps1)

# 4. Deploy updated code
cdk deploy

# 5. Verify deployment
aws lambda invoke \
  --function-name DailyStoicSender \
  --payload '{}' \
  response.json

cat response.json
```

---

## Coding Conventions

### Python Style

- **Python Version**: 3.12
- **Code Formatter**: Black (line length: 88)
- **Linter**: flake8
- **Type Checker**: mypy
- **Naming Conventions**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private members: `_leading_underscore`

### Type Hints

**Always use type hints** for function signatures:

```python
def get_quote_for_date(self, date: datetime) -> Dict[str, str]:
    """Get quote for specific date."""
    ...

def load_recipients_from_s3(bucket_name: str) -> List[str]:
    """Load recipient list from S3."""
    ...
```

Use `TypedDict` for structured dictionaries:

```python
from typing import TypedDict

class ThemeInfo(TypedDict):
    name: str
    description: str
```

### Logging

**Use structured logging** throughout:

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Good logging examples
logger.info(f"Loading quote for {date}")
logger.warning(f"Content validation issues: {validation}")
logger.error(f"Failed to send email to {recipient}: {e}")
logger.error(f"Fatal error: {e}", exc_info=True)  # Include stack trace
```

**Logging Levels**:
- `INFO`: Normal execution flow (quote loaded, email sent, etc.)
- `WARNING`: Unexpected but handled situations (validation issues, unusual formats)
- `ERROR`: Failures (API errors, S3 errors, email send failures)

### Error Handling

**Pattern**: Catch specific exceptions, log errors, and handle gracefully.

```python
# Good: Specific exception handling
try:
    response = s3_client.get_object(Bucket=bucket_name, Key='file.json')
    content = json.loads(response['Body'].read())
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchKey':
        logger.info("File not found, starting fresh")
        return default_value
    else:
        logger.error(f"S3 error: {e}")
        raise
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON: {e}")
    raise ValueError(f"Invalid JSON in file: {e}")
```

**Never swallow exceptions silently** unless intentional (e.g., continuing with other recipients).

### Documentation

**Use comprehensive docstrings** (Google style):

```python
def generate_reflection_only(
    quote: str,
    attribution: str,
    theme: str,
    api_key: str,
    previous_reflections: Optional[List[Dict[str, str]]] = None
) -> Optional[str]:
    """
    Generate a reflection based on a provided quote.

    Args:
        quote: The stoic quote to reflect upon
        attribution: The quote's attribution (e.g., "Marcus Aurelius - Meditations 5.1")
        theme: Monthly theme name
        api_key: Anthropic API key
        previous_reflections: List of previous quotes and reflections from this month

    Returns:
        The reflection text, or None if generation fails

    Raises:
        Exception: If API call fails or response is invalid
    """
```

### Testing Conventions

**Test file structure**: Mirror the source structure in `tests/`

```python
# tests/test_themes.py
import pytest
from lambda.themes import get_monthly_theme

class TestThemes:
    """Test cases for monthly themes."""

    def test_get_monthly_theme_january(self):
        """Test January theme."""
        theme = get_monthly_theme(1)
        assert theme["name"] == "Discipline and Self-Improvement"
        assert "habits" in theme["description"].lower()

    def test_get_monthly_theme_invalid_month_low(self):
        """Test invalid month (too low)."""
        with pytest.raises(ValueError):
            get_monthly_theme(0)
```

**Test naming**: `test_<function_name>_<scenario>`

**Use fixtures** for common setup:

```python
@pytest.fixture
def sample_quote():
    return {
        "quote": "Test quote",
        "attribution": "Marcus Aurelius - Meditations 5.1",
        "theme": "Discipline and Self-Improvement"
    }
```

---

## Testing Strategy

### Unit Tests

**Location**: `tests/` directory

**Test Coverage**:
- `test_themes.py`: Monthly theme functions
- `test_quote_tracker.py`: Quote history management
- `test_email_formatter.py`: Email formatting functions

**Running Tests**:
```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=lambda       # With coverage report
pytest tests/test_themes.py  # Specific file
```

### Integration Tests

**Quote Database Validation** (`validate_quotes.py`):
```bash
python validate_quotes.py
```

Validates:
- All 365 days have quotes
- No duplicate days
- Correct JSON structure
- Valid attribution format

**Quote Loader Test** (`test_quote_loader.py`):
```bash
python test_quote_loader.py
```

Tests quote loading from local config file (simulates S3).

### Manual Testing

**Test Lambda Function** (after deployment):
```bash
# Invoke Lambda manually
aws lambda invoke \
  --function-name DailyStoicSender \
  --payload '{}' \
  response.json

cat response.json
```

**Test Email Delivery**:
- Check recipient inbox
- Verify HTML rendering
- Test plain text fallback
- Check subject line format

---

## Configuration Management

### Environment Variables (Lambda)

Set in `infra/stoic_stack.py`:

```python
environment={
    "BUCKET_NAME": bucket.bucket_name,           # Auto-set by CDK
    "SENDER_EMAIL": "reflections@jamescmooney.com",
    "ANTHROPIC_API_KEY": anthropic_api_key,      # From cdk.json context
}
```

### CDK Context (`cdk.json`)

```json
{
  "context": {
    "anthropic_api_key": "sk-ant-...",           # REPLACE WITH ACTUAL KEY
    "sender_email": "reflections@jamescmooney.com",
    "sender_domain": "jamescmooney.com",
    "initial_recipient": "jamesmoon2@gmail.com"
  }
}
```

**Security Note**: API keys in `cdk.json` should be replaced with secure storage (AWS Secrets Manager) for production.

### S3 Configuration Files

**`config/stoic_quotes_365_days.json`** - 365-day quote database:
```json
{
  "january": [
    {
      "day": 1,
      "quote": "Quote text...",
      "attribution": "Marcus Aurelius - Meditations 5.1",
      "theme": "Discipline and Self-Improvement"
    }
  ],
  "february": [...],
  ...
}
```

**`config/recipients.json`** - Email recipient list:
```json
{
  "recipients": [
    "email1@example.com",
    "email2@example.com"
  ]
}
```

**`config/quote_history.json`** - Historical archive (auto-managed):
```json
{
  "quotes": [
    {
      "date": "2025-11-16",
      "quote": "Quote text...",
      "attribution": "Marcus Aurelius - Meditations 5.1",
      "theme": "Gratitude and Contentment",
      "reflection": "Full reflection text..."
    }
  ]
}
```

---

## Deployment Process

### First-Time Deployment

See `DEPLOYMENT.md` for complete step-by-step guide.

**Quick Summary**:

1. **Prerequisites**: AWS account, Anthropic API key, Python 3.12, Node.js, AWS CLI
2. **Setup**: Create venv, install dependencies, configure AWS CLI
3. **Configure**: Update `cdk.json` with API key
4. **Bootstrap**: `cdk bootstrap` (first time only)
5. **Deploy**: `cdk deploy`
6. **Upload Config**: Upload S3 files (quotes DB, recipients)
7. **Verify SES**: Verify sender domain in Amazon SES
8. **Test**: Invoke Lambda manually

### Updating Existing Deployment

**Updating Lambda Code**:
```bash
# 1. Edit code in lambda/ directory
# 2. Test locally: pytest
# 3. Rebuild package (Docker or build_lambda.ps1)
# 4. Deploy: cdk deploy
```

**Updating Configuration**:
```bash
# Get bucket name
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name DailyStoicStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

# Update recipients
aws s3 cp config/recipients.json s3://$BUCKET_NAME/

# Update quotes (CAREFUL - impacts daily rotation)
aws s3 cp config/stoic_quotes_365_days.json s3://$BUCKET_NAME/config/
```

**Updating Infrastructure**:
```bash
# 1. Edit infra/stoic_stack.py
# 2. Review changes: cdk diff
# 3. Deploy: cdk deploy
```

### Rolling Back Changes

```bash
# View stack history
aws cloudformation list-stacks

# If needed, redeploy previous version
git checkout <previous-commit>
cdk deploy
```

---

## Common Tasks

### Adding a New Recipient

```bash
# 1. Edit config/recipients.json locally
{
  "recipients": [
    "existing@example.com",
    "new-recipient@example.com"  # ADD THIS LINE
  ]
}

# 2. Upload to S3
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name DailyStoicStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

aws s3 cp config/recipients.json s3://$BUCKET_NAME/

# 3. Verify new recipient email in SES (if required)
aws ses verify-email-identity --email-address new-recipient@example.com

# 4. Test by invoking Lambda
aws lambda invoke \
  --function-name DailyStoicSender \
  --payload '{}' \
  response.json
```

### Changing the Daily Schedule

Edit `infra/stoic_stack.py`:

```python
# Change from 6 AM PST (14:00 UTC) to 7 AM PST (15:00 UTC)
schedule=events.Schedule.cron(
    minute="0",
    hour="15",  # CHANGE THIS
    month="*",
    week_day="*",
    year="*"
)
```

Then deploy: `cdk deploy`

### Updating the Anthropic Prompt

Edit `lambda/anthropic_client.py`, function `build_reflection_prompt()`.

**Example: Add instruction to include a practical exercise**:

```python
prompt = f"""You are a thoughtful teacher of stoic philosophy...

Write a reflection (150-250 words) that bridges ancient wisdom with contemporary challenges:

CONTENT FOCUS:
- Explain the quote's meaning in accessible language
- Connect it to real 2025 challenges
- Offer practical, actionable guidance the reader can apply today
- Include a simple daily exercise or practice  # ADD THIS LINE
...
"""
```

After editing:
```bash
pytest                    # Test locally
# Rebuild Lambda package
cdk deploy                # Deploy update
```

### Adding a New Monthly Theme

**Not recommended** - changing themes breaks the 365-day predictable rotation. If necessary:

1. Edit `lambda/themes.py`
2. Update all 365 quotes in `config/stoic_quotes_365_days.json` to match new themes
3. Re-upload quotes DB to S3
4. Clear quote history (optional): `aws s3 rm s3://$BUCKET_NAME/quote_history.json`

### Monitoring Costs

```bash
# Check AWS Cost Explorer via CLI
aws ce get-cost-and-usage \
  --time-period Start=2025-11-01,End=2025-11-30 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Expected monthly cost breakdown:
# - Lambda: $0.00 (free tier)
# - EventBridge: $0.00 (free tier)
# - S3: $0.00 (negligible)
# - SES: $0.003 (30 emails * $0.0001)
# - Anthropic API: $0.18 (30 days * $0.006)
# Total: ~$0.18/month
```

### Viewing Logs

```bash
# View recent Lambda logs
aws logs tail /aws/lambda/DailyStoicSender --follow

# View logs for specific date
aws logs tail /aws/lambda/DailyStoicSender --since 1d

# Search logs for errors
aws logs tail /aws/lambda/DailyStoicSender --filter-pattern "ERROR"
```

---

## Troubleshooting

### Lambda Function Fails to Execute

**Check CloudWatch Logs**:
```bash
aws logs tail /aws/lambda/DailyStoicSender --follow
```

**Common Issues**:

1. **Missing Environment Variables**:
   - Error: `Missing required environment variables`
   - Fix: Verify `BUCKET_NAME`, `SENDER_EMAIL`, `ANTHROPIC_API_KEY` are set in Lambda configuration

2. **S3 Access Denied**:
   - Error: `AccessDenied` when reading S3 files
   - Fix: Verify Lambda IAM role has S3 read/write permissions (check `infra/stoic_stack.py`)

3. **SES Unverified Email**:
   - Error: `Email address is not verified`
   - Fix: Verify sender email in SES: `aws ses verify-email-identity --email-address <email>`

4. **Anthropic API Error**:
   - Error: `Invalid API key` or `Rate limit exceeded`
   - Fix: Verify API key in `cdk.json`, check Anthropic account status

### Emails Not Being Delivered

**Check SES Sending Statistics**:
```bash
aws ses get-send-statistics
```

**Common Issues**:

1. **SES Sandbox Mode**:
   - Only verified emails can receive messages in sandbox mode
   - Request production access: AWS Console → SES → Account Dashboard → Request Production Access

2. **Bounced Emails**:
   - Check bounce notifications in SES console
   - Verify recipient email addresses are valid

3. **Spam Folder**:
   - Emails may be marked as spam
   - Improve deliverability: Set up SPF, DKIM, DMARC records for sender domain

### Quote Database Issues

**Validate Quote Database**:
```bash
python validate_quotes.py
```

**Common Issues**:

1. **Missing Days**:
   - Error: `Missing days: [('february', 29), ...]`
   - Fix: Add missing quotes to `config/stoic_quotes_365_days.json`

2. **Duplicate Days**:
   - Error: `Duplicate days: [('march', 15), ...]`
   - Fix: Remove duplicate entries from quote database

3. **Invalid JSON**:
   - Error: `Invalid JSON in quotes database`
   - Fix: Validate JSON syntax (use JSON linter)

### CDK Deployment Failures

**Check CDK Diff Before Deploy**:
```bash
cdk diff
```

**Common Issues**:

1. **Bootstrap Not Run**:
   - Error: `This stack uses assets, so the toolkit stack must be deployed`
   - Fix: Run `cdk bootstrap`

2. **Insufficient IAM Permissions**:
   - Error: `User is not authorized to perform: cloudformation:CreateStack`
   - Fix: Verify AWS IAM user has CloudFormation, Lambda, S3, EventBridge, IAM permissions

3. **Resource Name Conflicts**:
   - Error: `Resource already exists`
   - Fix: Delete existing resources or use different stack name

### Anthropic API Issues

**Test API Key Locally**:
```python
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.content[0].text)
```

**Common Issues**:

1. **Invalid API Key**:
   - Error: `Invalid API key`
   - Fix: Verify key in `cdk.json`, regenerate key in Anthropic Console

2. **Rate Limit Exceeded**:
   - Error: `Rate limit exceeded`
   - Fix: Increase timeout, retry with exponential backoff, check Anthropic plan limits

3. **Timeout**:
   - Error: `Request timeout`
   - Fix: Increase Lambda timeout (currently 60s) or API timeout (currently 25s)

---

## Best Practices for AI Assistants

### When Making Changes

1. **Read Before Writing**: Always read existing files before modifying them
2. **Test Locally First**: Run `pytest` before deploying
3. **Use Type Hints**: Maintain type safety with Python type annotations
4. **Log Appropriately**: Use structured logging for debugging
5. **Preserve Patterns**: Follow existing code patterns and conventions
6. **Update Documentation**: Keep README, ARCHITECTURE, and this file in sync

### When Adding Features

1. **Check Dependencies**: Ensure new Python packages are added to `requirements.txt` AND `lambda/requirements.txt`
2. **Update CDK Stack**: If new AWS resources are needed, modify `infra/stoic_stack.py`
3. **Add Tests**: Write unit tests for new functionality
4. **Update Prompt**: If changing AI behavior, carefully modify prompt in `anthropic_client.py`
5. **Preserve Themes**: Maintain consistency with monthly theme system

### When Debugging

1. **Check CloudWatch Logs**: First place to look for Lambda errors
2. **Validate Locally**: Use `test_quote_loader.py` and `validate_quotes.py`
3. **Isolate Components**: Test individual modules (quote loader, email formatter, etc.)
4. **Check S3 Files**: Verify config files exist and have correct format
5. **Verify Permissions**: Ensure IAM roles have necessary permissions

### Security Considerations

1. **Never Commit API Keys**: Keep `cdk.json` with actual keys in `.gitignore`
2. **Use Secrets Manager**: For production, move API keys to AWS Secrets Manager
3. **Validate Inputs**: Always validate data from S3 before using
4. **Escape HTML**: Use `html.escape()` for user-provided content (already implemented)
5. **Least Privilege**: Lambda IAM role should have minimal required permissions

---

## Additional Resources

### Documentation Files

- **README.md**: Project overview and quick start
- **ARCHITECTURE.md**: Detailed architecture and design decisions
- **DEPLOYMENT.md**: Step-by-step deployment guide
- **MAINTENANCE.md**: Operations, monitoring, and maintenance procedures
- **prd.md**: Product requirements document
- **projectplan.md**: Original implementation plan

### External Documentation

- **AWS CDK**: https://docs.aws.amazon.com/cdk/
- **AWS Lambda**: https://docs.aws.amazon.com/lambda/
- **Amazon SES**: https://docs.aws.amazon.com/ses/
- **Anthropic API**: https://docs.anthropic.com/
- **Python 3.12**: https://docs.python.org/3.12/

### Useful Commands Reference

```bash
# CDK Commands
cdk bootstrap              # Bootstrap CDK (first time)
cdk synth                  # Synthesize CloudFormation template
cdk diff                   # Show differences from deployed stack
cdk deploy                 # Deploy stack to AWS
cdk destroy                # Delete stack from AWS

# Testing Commands
pytest                     # Run all unit tests
pytest -v                  # Verbose test output
pytest --cov=lambda        # Test with coverage
python validate_quotes.py  # Validate quote database
python test_quote_loader.py # Test quote loading

# AWS CLI Commands
aws lambda invoke --function-name DailyStoicSender --payload '{}' response.json
aws logs tail /aws/lambda/DailyStoicSender --follow
aws s3 ls s3://<bucket-name>/
aws ses verify-email-identity --email-address <email>
aws cloudformation describe-stacks --stack-name DailyStoicStack

# Git Commands
git status
git add .
git commit -m "Description"
git push
git checkout -b feature/name
```

---

## Conclusion

This document should give you (AI assistant) a comprehensive understanding of the MorningMeditations codebase. When working on this project:

- **Understand the flow**: EventBridge → Lambda → (S3 + Anthropic API) → SES
- **Respect the 365-day cycle**: Quote database is carefully curated for predictable rotation
- **Maintain theme consistency**: Monthly themes are central to the user experience
- **Test thoroughly**: Use pytest, validate quotes, test locally before deploying
- **Follow conventions**: Type hints, logging, error handling, documentation
- **Preserve quality**: This is a production service delivering daily value to users

For questions or clarifications, refer to the other documentation files or examine the code directly. Happy coding!
