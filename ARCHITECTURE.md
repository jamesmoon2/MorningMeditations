# Daily Stoic Reflection - System Architecture & Data Flow

This document provides a comprehensive view of the system architecture, data flow, and all services/endpoints involved in the Daily Stoic Reflection service.

## System Architecture Diagram

```mermaid
graph TB
    subgraph "AWS Cloud Infrastructure"
        subgraph "Trigger Layer"
            EB[EventBridge Rule<br/>DailyStoicTrigger<br/>cron: 0 14 * * ? *<br/>6:00 AM PST / 7:00 AM PDT]
        end

        subgraph "Compute Layer"
            Lambda[AWS Lambda Function<br/>DailyStoicSender<br/>Python 3.12 Runtime<br/>256MB Memory / 60s Timeout]

            subgraph "Lambda Modules"
                Handler[handler.py<br/>lambda_handler]
                Themes[themes.py<br/>get_monthly_theme]
                QuoteLoader[quote_loader.py<br/>QuoteLoader class]
                Tracker[quote_tracker.py<br/>QuoteTracker class]
                Anthropic[anthropic_client.py<br/>generate_reflection_only]
                Formatter[email_formatter.py<br/>format_html_email]
            end
        end

        subgraph "Storage Layer"
            S3[S3 Bucket<br/>State Management<br/>Versioned + Encrypted]

            subgraph "S3 Objects"
                QuotesDB[stoic_quotes_365_days.json<br/>365 curated quotes]
                History[quote_history.json<br/>Historical archive]
                Recipients[recipients.json<br/>Email distribution list]
            end
        end

        subgraph "Email Layer"
            SES[Amazon SES<br/>jamescmooney.com<br/>DKIM Enabled]
        end

        subgraph "Monitoring Layer"
            CW[CloudWatch Logs<br/>/aws/lambda/DailyStoicSender<br/>7-day retention]
        end
    end

    subgraph "External Services"
        AnthropicAPI[Anthropic API<br/>api.anthropic.com/v1/messages<br/>Model: claude-sonnet-4-5-20250929<br/>Max Tokens: 2000]
    end

    subgraph "Email Recipients"
        Gmail[Gmail Inbox<br/>jamesmoon2@gmail.com<br/>+ Other Recipients]
    end

    %% Flow connections
    EB -->|Scheduled Trigger| Lambda
    Lambda -->|Read| QuotesDB
    Lambda -->|Read| History
    Lambda -->|Read| Recipients
    Lambda -->|HTTP POST| AnthropicAPI
    AnthropicAPI -->|Reflection JSON| Lambda
    Lambda -->|Archive| History
    Lambda -->|SendEmail API| SES
    SES -->|HTML + Plain Text| Gmail
    Lambda -->|Log Events| CW

    %% Storage connections
    S3 -.->|Contains| QuotesDB
    S3 -.->|Contains| History
    S3 -.->|Contains| Recipients

    %% Module connections
    Lambda -.->|Orchestrates| Handler
    Handler -.->|Uses| Themes
    Handler -.->|Uses| QuoteLoader
    Handler -.->|Uses| Tracker
    Handler -.->|Uses| Anthropic
    Handler -.->|Uses| Formatter

    style EB fill:#FF9900
    style Lambda fill:#FF9900
    style S3 fill:#569A31
    style SES fill:#DD344C
    style CW fill:#FF9900
    style AnthropicAPI fill:#D4B5A0
    style Gmail fill:#4285F4
```

## Detailed Data Flow Sequence

```mermaid
sequenceDiagram
    participant EB as EventBridge<br/>DailyStoicTrigger
    participant Lambda as Lambda Function<br/>handler.lambda_handler()
    participant Themes as themes.py<br/>get_monthly_theme()
    participant QuoteLoader as quote_loader.py<br/>QuoteLoader
    participant S3 as S3 Bucket
    participant Tracker as quote_tracker.py<br/>QuoteTracker
    participant Claude as Anthropic API<br/>claude-sonnet-4-5
    participant Formatter as email_formatter.py
    participant SES as Amazon SES
    participant User as Email Recipients
    participant CW as CloudWatch Logs

    Note over EB: Daily at 14:00 UTC<br/>(6 AM PST / 7 AM PDT)
    EB->>Lambda: Trigger Scheduled Event
    Lambda->>CW: Log: Starting Daily Stoic Reflection

    Note over Lambda: Step 1: Initialize Environment
    Lambda->>Lambda: Get BUCKET_NAME env var
    Lambda->>Lambda: Get SENDER_EMAIL env var
    Lambda->>Lambda: Get ANTHROPIC_API_KEY env var
    Lambda->>Lambda: Get current date/month

    Note over Lambda: Step 2: Determine Theme
    Lambda->>Themes: get_monthly_theme(month)
    Themes-->>Lambda: Return theme_info{name, description}
    Lambda->>CW: Log: Theme for current month

    Note over Lambda: Step 3: Load Today's Quote
    Lambda->>QuoteLoader: QuoteLoader(bucket_name)
    QuoteLoader->>S3: GET config/stoic_quotes_365_days.json
    S3-->>QuoteLoader: Return 365-day quotes database
    QuoteLoader->>QuoteLoader: get_quote_for_date(current_date)
    Note over QuoteLoader: Extract month/day<br/>Handle leap year (Feb 29→28)
    QuoteLoader-->>Lambda: Return {quote, attribution, theme}
    Lambda->>CW: Log: Loaded quote for date

    Note over Lambda: Step 4: Load Recipients
    Lambda->>S3: GET recipients.json
    S3-->>Lambda: Return recipients list
    Lambda->>CW: Log: Found N recipients

    Note over Lambda: Step 5: Generate Reflection
    Lambda->>Claude: POST /v1/messages<br/>build_reflection_prompt(quote, attribution, theme)
    Note over Claude: Model: claude-sonnet-4-5-20250929<br/>Max Tokens: 2000<br/>Temperature: 1.0
    Claude->>Claude: Generate reflection only<br/>(quote provided)
    Claude-->>Lambda: JSON: {reflection}
    Lambda->>Lambda: parse_reflection_response()
    Lambda->>CW: Log: Generated reflection (N chars)

    Note over Lambda: Step 6: Archive to History
    Lambda->>Tracker: QuoteTracker(bucket_name)
    Tracker->>S3: GET quote_history.json
    S3-->>Tracker: Return history JSON
    Lambda->>Tracker: add_quote(date, quote, attribution, reflection, theme)
    Note over Tracker: Store complete record<br/>with reflection preview
    Tracker->>Tracker: cleanup_old_quotes(keep_days=400)
    Tracker->>S3: PUT quote_history.json<br/>(Updated archive)
    S3-->>Tracker: Confirm write
    Lambda->>CW: Log: History updated, total entries

    Note over Lambda: Step 7: Format Email
    Lambda->>Formatter: format_html_email(quote, attribution, reflection, theme)
    Formatter-->>Lambda: Return HTML content
    Lambda->>Formatter: format_plain_text_email(quote, attribution, reflection)
    Formatter-->>Lambda: Return plain text content
    Lambda->>Formatter: create_email_subject(theme)
    Formatter-->>Lambda: Return subject line

    Note over Lambda: Step 8: Send Emails
    loop For each recipient
        Lambda->>SES: SendEmail API<br/>Source: reflections@jamescmooney.com<br/>Destination: recipient<br/>HTML + Text body
        SES->>SES: DKIM sign message
        SES->>User: Deliver email via SMTP
        User-->>SES: Accept delivery
        SES-->>Lambda: MessageId confirmation
        Lambda->>CW: Log: Successfully sent to recipient
    end

    Note over Lambda: Step 9: Return Success
    Lambda->>CW: Log: Email sending complete
    Lambda-->>EB: Return {statusCode: 200, body: {success_count, date, theme, attribution}}
```

## Service Endpoints & Configuration

### AWS Services

| Service | Endpoint/Resource | Configuration |
|---------|------------------|---------------|
| **EventBridge** | `events.us-west-2.amazonaws.com` | Rule: `DailyStoicTrigger`<br/>Schedule: `cron(0 14 * * ? *)` |
| **Lambda** | `lambda.us-west-2.amazonaws.com` | Function: `DailyStoicSender`<br/>Runtime: `python3.12`<br/>Handler: `handler.lambda_handler` |
| **S3** | `s3.us-west-2.amazonaws.com` | Bucket: Auto-generated name<br/>Objects: `quote_history.json`, `recipients.json` |
| **SES** | `email.us-west-2.amazonaws.com` | Domain: `jamescmooney.com`<br/>Sender: `reflections@jamescmooney.com`<br/>API: `SendEmail` |
| **CloudWatch Logs** | `logs.us-west-2.amazonaws.com` | Log Group: `/aws/lambda/DailyStoicSender`<br/>Retention: 7 days |

### External API Endpoints

| Service | Endpoint | Method | Request Details |
|---------|----------|--------|-----------------|
| **Anthropic Messages API** | `https://api.anthropic.com/v1/messages` | POST | **Model**: `claude-sonnet-4-5-20250929`<br/>**Max Tokens**: 2000<br/>**Temperature**: 1.0<br/>**Timeout**: 25 seconds<br/>**Headers**: `x-api-key`, `anthropic-version: 2023-06-01` |

### S3 Data Objects

#### stoic_quotes_365_days.json
```json
{
  "january": [
    {
      "day": 1,
      "theme": "Discipline and Self-Improvement",
      "quote": "At dawn, when you have trouble getting out of bed...",
      "attribution": "Marcus Aurelius - Meditations 5.1"
    }
  ],
  "february": [...],
  ...
}
```
**Operations**:
- `s3:GetObject` - Read by QuoteLoader.load_quotes_database()
- Contains all 365 curated quotes, organized by month

#### quote_history.json
```json
{
  "quotes": [
    {
      "date": "2025-10-26",
      "quote": "The present is the only thing...",
      "attribution": "Marcus Aurelius - Meditations 2.14",
      "theme": "Mortality and Impermanence",
      "reflection_preview": "This powerful reminder from Marcus Aurelius cuts straight to the heart of one of stoicism's..."
    }
  ]
}
```
**Operations**:
- `s3:GetObject` - Read by QuoteTracker.load_history()
- `s3:PutObject` - Write by QuoteTracker.save_history()
- Serves as complete historical archive with reflection previews

#### recipients.json
```json
{
  "recipients": [
    "jamesmoon2@gmail.com"
  ]
}
```
**Operations**:
- `s3:GetObject` - Read by load_recipients_from_s3()

## Lambda Function Module Architecture

```mermaid
graph LR
    subgraph "Lambda Handler Entry Point"
        Main[handler.py<br/>lambda_handler]
    end

    subgraph "Core Modules"
        T[themes.py<br/>MONTHLY_THEMES dict<br/>get_monthly_theme]
        QL[quote_loader.py<br/>QuoteLoader class<br/>load_quotes_database<br/>get_quote_for_date]
        QT[quote_tracker.py<br/>QuoteTracker class<br/>load/save_history<br/>add_quote (archival)]
        AC[anthropic_client.py<br/>build_reflection_prompt<br/>call_anthropic_api<br/>generate_reflection_only]
        EF[email_formatter.py<br/>format_html_email<br/>format_plain_text_email<br/>create_email_subject]
    end

    subgraph "AWS SDK Clients"
        Boto3S3[boto3.client: s3<br/>get_object<br/>put_object]
        Boto3SES[boto3.client: ses<br/>send_email]
    end

    subgraph "External Libraries"
        AnthropicSDK[anthropic.Anthropic<br/>messages.create]
    end

    Main -->|Import & Call| T
    Main -->|Import & Call| QL
    Main -->|Import & Call| QT
    Main -->|Import & Call| AC
    Main -->|Import & Call| EF

    QL -->|Uses| Boto3S3
    QT -->|Uses| Boto3S3
    Main -->|Uses| Boto3S3
    Main -->|Uses| Boto3SES
    AC -->|Uses| AnthropicSDK

    style Main fill:#FF9900
    style T fill:#4A90E2
    style QL fill:#4A90E2
    style QT fill:#4A90E2
    style AC fill:#4A90E2
    style EF fill:#4A90E2
    style Boto3S3 fill:#569A31
    style Boto3SES fill:#DD344C
    style AnthropicSDK fill:#D4B5A0
```

## Data Flow by Step

### Step 1: Initialization (handler.py:50-73)
```
Environment Variables:
  - BUCKET_NAME → S3 bucket for state
  - SENDER_EMAIL → reflections@jamescmooney.com
  - ANTHROPIC_API_KEY → sk-ant-...
  - AWS_REGION → us-west-2

Current State:
  - current_date = datetime.now()
  - current_month = date.month (1-12)
  - theme_info = get_monthly_theme(current_month)
```

### Step 2: Load Today's Quote (handler.py:76-84)
```
S3 Read Operation:
  Bucket: {BUCKET_NAME}
  Key: config/stoic_quotes_365_days.json

Processing:
  - QuoteLoader.load_quotes_database()
  - QuoteLoader.get_quote_for_date(current_date)
  - Extract month name and day number
  - Handle leap year (Feb 29 → Feb 28)
  - Return matching quote

Returns:
  {
    "quote": "Stoic quote text",
    "attribution": "Author - Work Section",
    "theme": "Monthly theme"
  }
```

### Step 3: Load Recipients (handler.py:86-91)
```
S3 Read Operation:
  Bucket: {BUCKET_NAME}
  Key: recipients.json

Returns:
  Array of email addresses
```

### Step 4: Generate Reflection (handler.py:93-105)
```
API Call:
  Endpoint: https://api.anthropic.com/v1/messages
  Method: POST

Request Body:
  {
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 2000,
    "temperature": 1.0,
    "messages": [
      {
        "role": "user",
        "content": "{prompt with provided quote, attribution, and theme}"
      }
    ]
  }

Response:
  {
    "reflection": "250-450 word reflection"
  }
```

### Step 5: Archive to History (handler.py:113-124)
```
S3 Operations:
  Read: quote_history.json
  Write: quote_history.json (updated)

Data:
  - Append new entry: {date, quote, attribution, theme, reflection_preview}
  - reflection_preview = first 100 chars of reflection
  - Cleanup entries older than 400 days
  - Write updated JSON back to S3
  - Serves as complete historical archive
```

### Step 6: Send Emails (handler.py:122-147)
```
SES API Call (per recipient):
  Operation: SendEmail

Parameters:
  - Source: reflections@jamescmooney.com
  - Destination.ToAddresses: [recipient]
  - Message.Subject: "Daily Stoic Reflection: {theme}"
  - Message.Body.Html: {formatted HTML}
  - Message.Body.Text: {plain text fallback}

Response:
  - MessageId: AWS message identifier
```

## IAM Permissions Required

```json
{
  "Lambda Execution Role": {
    "S3 Permissions": [
      "s3:GetObject",
      "s3:PutObject"
    ],
    "Resources": [
      "arn:aws:s3:::{bucket-name}/*"
    ],
    "SES Permissions": [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ],
    "Resources": ["*"],
    "CloudWatch Logs": [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
  }
}
```

## Cost Breakdown by Endpoint

| Service/Endpoint | Monthly Usage | Unit Cost | Monthly Cost |
|-----------------|---------------|-----------|--------------|
| EventBridge Rule Invocations | 30 triggers | Free tier | $0.00 |
| Lambda Invocations | 30 executions × 10s | Free tier | $0.00 |
| S3 GET Requests | 60 requests | $0.0004/1K | $0.00 |
| S3 PUT Requests | 30 requests | $0.005/1K | $0.00 |
| S3 Storage | ~1 MB | $0.023/GB | $0.00 |
| SES SendEmail API | 30 emails | $0.10/1K | $0.003 |
| Anthropic Messages API | 30 calls × 2K tokens | $3.00/1M tokens | $0.18 |
| CloudWatch Logs | ~50 MB | Free tier (5GB) | $0.00 |
| **Total** | | | **~$0.18/month** |

## Performance Metrics

| Metric | Typical Value | Maximum |
|--------|---------------|---------|
| **Lambda Execution Time** | 8-12 seconds | 60 seconds (timeout) |
| **Anthropic API Response Time** | 3-8 seconds | 25 seconds (timeout) |
| **S3 Read Latency** | 50-100 ms | - |
| **S3 Write Latency** | 100-200 ms | - |
| **SES Delivery Time** | 30-120 seconds | - |
| **End-to-End Time** | 10-15 seconds | - |
| **Lambda Memory Usage** | 100-150 MB | 256 MB (allocated) |

## Error Handling & Retry Logic

```mermaid
graph TD
    Start[Lambda Invocation] --> ValidateEnv{Environment<br/>Variables OK?}
    ValidateEnv -->|No| Error1[Return 500 Error]
    ValidateEnv -->|Yes| LoadHistory

    LoadHistory[Load S3 History] --> HistoryOK{History<br/>Loaded?}
    HistoryOK -->|NoSuchKey| CreateEmpty[Create Empty History]
    HistoryOK -->|Error| Error2[Return 500 Error]
    HistoryOK -->|Success| LoadRecipients
    CreateEmpty --> LoadRecipients

    LoadRecipients[Load Recipients] --> RecipientsOK{Recipients<br/>Found?}
    RecipientsOK -->|No| Error3[Return 500 Error]
    RecipientsOK -->|Yes| CallAPI

    CallAPI[Call Anthropic API] --> APIOK{API<br/>Success?}
    APIOK -->|Timeout/Error| Error4[Return 500 Error]
    APIOK -->|Success| UpdateHistory

    UpdateHistory[Update S3 History] --> SendEmails

    SendEmails[Send Emails] --> EmailLoop{For Each<br/>Recipient}
    EmailLoop -->|Next| TrySend[Try SES SendEmail]
    TrySend --> SendOK{Success?}
    SendOK -->|Yes| CountSuccess[success_count++]
    SendOK -->|No| CountFailure[failure_count++]
    CountSuccess --> MoreRecipients{More<br/>Recipients?}
    CountFailure --> LogError[Log Error]
    LogError --> MoreRecipients
    MoreRecipients -->|Yes| EmailLoop
    MoreRecipients -->|No| Return200[Return 200 Success]

    style Error1 fill:#E74C3C
    style Error2 fill:#E74C3C
    style Error3 fill:#E74C3C
    style Error4 fill:#E74C3C
    style Return200 fill:#27AE60
    style CountSuccess fill:#27AE60
    style CountFailure fill:#E67E22
```

## Monthly Themes Configuration

The system uses a predefined theme for each month (themes.py:17-66):

| Month | Theme | Description |
|-------|-------|-------------|
| January | Discipline and Self-Improvement | Building habits, self-control, starting fresh |
| February | Relationships and Community | Connections to others, love, friendship |
| March | Resilience and Adversity | Facing challenges, mental toughness |
| April | Nature and Acceptance | Living in accordance with nature |
| May | Virtue and Character | Four cardinal virtues |
| June | Wisdom and Philosophy | Continuous learning, philosophical practice |
| July | Freedom and Autonomy | Inner freedom, independence of mind |
| August | Patience and Endurance | Long-term thinking, persistence |
| September | Purpose and Calling | Finding meaning, living deliberately |
| October | Mortality and Impermanence | Memento mori, perspective on death |
| November | Gratitude and Contentment | Appreciating what we have |
| December | Reflection and Legacy | Year-end contemplation, what we leave behind |

## Security Architecture

```mermaid
graph TB
    subgraph "Secrets Management"
        CDK[cdk.json context<br/>anthropic_api_key]
        Env[Lambda Environment Variables<br/>ANTHROPIC_API_KEY]
    end

    subgraph "AWS IAM"
        Role[Lambda Execution Role]
        S3Policy[S3 Read/Write Policy]
        SESPolicy[SES Send Email Policy]
        CWPolicy[CloudWatch Logs Policy]
    end

    subgraph "Network Security"
        S3Encryption[S3 Server-Side Encryption<br/>AES-256]
        S3Block[S3 Block Public Access<br/>BLOCK_ALL]
        S3Versioning[S3 Versioning Enabled]
    end

    subgraph "SES Security"
        DKIM[DKIM Signing Enabled]
        DomainVerification[Domain Verification<br/>jamescmooney.com]
    end

    CDK -->|Deploy| Env
    Env -->|Used By| Lambda
    Lambda -->|Assumes| Role
    Role -->|Attached| S3Policy
    Role -->|Attached| SESPolicy
    Role -->|Attached| CWPolicy

    S3Policy -->|Protects| S3Encryption
    S3Policy -->|Enforces| S3Block

    style CDK fill:#E67E22
    style Env fill:#27AE60
    style Role fill:#3498DB
    style S3Encryption fill:#27AE60
    style DKIM fill:#27AE60
```

## Monitoring & Logging Points

### CloudWatch Log Events (handler.py)

| Log Point | Line | Message | Level |
|-----------|------|---------|-------|
| Start | 47 | "Starting Daily Stoic Reflection generation" | INFO |
| Environment | 60-61 | "Using bucket: {bucket_name}" | INFO |
| Theme | 71-73 | "Date/Month/Theme info" | INFO |
| Quote Loaded | 77-84 | "Loading today's quote from database..." | INFO |
| Quote Found | 84 | "Loaded quote for {date}: {attribution}" | INFO |
| Recipients | 88 | "Found {n} recipients" | INFO |
| API Call | 94 | "Generating reflection via Anthropic API..." | INFO |
| Generated | 105 | "Generated reflection ({n} chars)" | INFO |
| History Update | 113 | "Updating quote history..." | INFO |
| History Saved | 124 | "History updated. Total entries: {n}" | INFO |
| Email Start | 127 | "Sending emails..." | INFO |
| Email Success | 142 | "Successfully sent email to {recipient}" | INFO |
| Email Failure | 146 | "Failed to send email to {recipient}: {error}" | ERROR |
| Complete | 150-152 | "Email sending complete. Success/Failed counts" | INFO |
| Fatal Error | 167 | "Fatal error in lambda_handler: {error}" | ERROR |

---

**Document Version**: 2.0
**Last Updated**: 2025-10-27
**Changes**: Updated for simplified quote system using pre-drafted 365-day database
