# MorningMeditations

Daily Stoic Reflection Email Service - Automated philosophical wisdom delivered every morning.

## Overview

An automated service that delivers daily stoic philosophical reflections via email. Each morning at 6:00 AM Pacific Time, the system loads a curated quote from a 365-day database and uses Claude (Anthropic's AI) to write an original reflection, themed by month.

## Features

- **Daily Delivery**: Automated emails at 6:00 AM PT
- **Curated Quotes**: 365 pre-selected classical stoic quotes (one for each day)
- **AI-Generated Reflections**: Fresh, unique reflections using Claude Sonnet 4.5
- **Monthly Themes**: 12 distinct themes throughout the year
- **Classical Sources**: Quotes from Marcus Aurelius, Epictetus, Seneca, and Musonius Rufus
- **Predictable Rotation**: 365-day quote cycle ensures variety and consistency
- **Beautiful HTML**: Responsive email formatting optimized for all devices
- **Cost-Effective**: Runs for ~$0.18/month

## Architecture

```
AWS Cloud
├── EventBridge (Daily 6 AM PT trigger)
├── Lambda (Python 3.12)
│   ├── Load daily quote from 365-day database
│   ├── Generate reflection via Anthropic API
│   ├── Archive to quote history in S3
│   └── Send formatted emails via SES
├── S3 (State management)
│   ├── stoic_quotes_365_days.json (365 curated quotes)
│   ├── quote_history.json (archival record)
│   └── recipients.json
└── SES (Email delivery from jamescmooney.com)
```

## Tech Stack

- **Infrastructure**: AWS (Lambda, EventBridge, SES, S3)
- **IaC**: AWS CDK with Python
- **Runtime**: Python 3.12
- **AI Model**: Anthropic Claude Sonnet 4.5
- **Email**: HTML via Amazon SES

## Project Structure

```
daily-stoic-reflection/
├── lambda/              # Lambda function code
│   ├── handler.py       # Main entry point
│   ├── quote_loader.py  # Loads daily quotes from 365-day database
│   ├── anthropic_client.py  # Generates reflections via API
│   ├── email_formatter.py
│   ├── quote_tracker.py  # Archives history
│   └── themes.py
├── infra/              # AWS CDK infrastructure
│   └── stoic_stack.py
├── config/             # Configuration files
│   ├── stoic_quotes_365_days.json  # 365 curated quotes
│   ├── recipients.json
│   └── quote_history.json  # Historical archive
├── tests/              # Unit tests
├── validate_quotes.py  # Validates 365-day database
├── test_quote_loader.py  # Tests quote loading
└── app.py              # CDK app entry point
```

## Setup

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete setup instructions.

### Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure

# Deploy infrastructure
cdk bootstrap  # First time only
cdk deploy
```

## Monthly Themes

1. **January**: Discipline and Self-Improvement
2. **February**: Relationships and Community
3. **March**: Resilience and Adversity
4. **April**: Nature and Acceptance
5. **May**: Virtue and Character
6. **June**: Wisdom and Philosophy
7. **July**: Freedom and Autonomy
8. **August**: Patience and Endurance
9. **September**: Purpose and Calling
10. **October**: Mortality and Impermanence
11. **November**: Gratitude and Contentment
12. **December**: Reflection and Legacy

## Maintenance

See [MAINTENANCE.md](MAINTENANCE.md) for ongoing maintenance instructions.

### Adding Recipients

```bash
# Edit config/recipients.json
# Upload to S3
aws s3 cp config/recipients.json s3://YOUR-BUCKET/recipients.json
```

## Cost Breakdown

| Service | Monthly Cost |
|---------|-------------|
| Lambda | $0.00 (free tier) |
| EventBridge | $0.00 (free tier) |
| S3 | $0.00 (negligible) |
| SES | $0.003 |
| Anthropic API | $0.18 |
| **Total** | **~$0.18/month** |

## Documentation

- [prd.md](prd.md) - Complete Product Requirements Document
- [projectplan.md](projectplan.md) - Implementation Project Plan
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment Guide
- [MAINTENANCE.md](MAINTENANCE.md) - Maintenance Guide

## License

Personal project by James Mooney