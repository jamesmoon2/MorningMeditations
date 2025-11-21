# MorningMeditations

Daily Stoic Reflection Email Service - Automated philosophical wisdom delivered every morning.

## Overview

An automated service that delivers daily stoic philosophical reflections via email. Each morning at 6:00 AM Pacific Time, the system loads a curated quote from a 365-day database and uses Claude (Anthropic's AI) to write an original reflection, themed by month.

## Features

- **Daily Delivery**: Automated emails at 6:00 AM PT
- **Public API**: REST API for accessing reflections (perfect for hardware devices)
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
├── Lambda - DailyStoicSender (Python 3.12)
│   ├── Load daily quote from 365-day database
│   ├── Generate reflection via Anthropic API
│   ├── Archive to quote history in S3
│   └── Send formatted emails via SES
├── API Gateway (Public REST API)
│   ├── GET /reflection/today
│   └── GET /reflection/{date}
├── Lambda - ReflectionApiHandler (Python 3.12)
│   └── Serve reflections from S3 (read-only)
├── S3 (State management)
│   ├── stoic_quotes_365_days.json (365 curated quotes)
│   ├── quote_history.json (archival record)
│   └── recipients.json
└── SES (Email delivery from jamescmooney.com)
```

## Tech Stack

- **Infrastructure**: AWS (Lambda, API Gateway, EventBridge, SES, S3)
- **IaC**: AWS CDK with Python
- **Runtime**: Python 3.12
- **AI Model**: Anthropic Claude Sonnet 4.5
- **Email**: HTML via Amazon SES
- **API**: REST API via Amazon API Gateway

## Project Structure

```
daily-stoic-reflection/
├── lambda/              # Lambda function code
│   ├── handler.py       # Main entry point (daily email)
│   ├── api_handler.py   # API endpoint handler
│   ├── quote_loader.py  # Loads daily quotes from 365-day database
│   ├── anthropic_client.py  # Generates reflections via API
│   ├── email_formatter.py
│   ├── quote_tracker.py  # Archives history
│   └── themes.py
├── infra/              # AWS CDK infrastructure
│   └── stoic_stack.py  # Includes API Gateway + Lambda
├── config/             # Configuration files
│   ├── stoic_quotes_365_days.json  # 365 curated quotes
│   ├── recipients.json
│   └── quote_history.json  # Historical archive
├── tests/              # Unit tests
├── build_lambda.sh     # Build Lambda deployment package
├── validate_quotes.py  # Validates 365-day database
├── test_quote_loader.py  # Tests quote loading
├── API_DOCUMENTATION.md  # API reference
├── API_DEPLOYMENT_GUIDE.md  # API deployment guide
└── app.py              # CDK app entry point
```

## API Access

The service provides a public REST API for accessing reflections programmatically - perfect for hardware devices, mobile apps, or web integrations.

### Endpoints

- `GET /reflection/today` - Returns today's reflection
- `GET /reflection/{date}` - Returns reflection for a specific date (YYYY-MM-DD)

### Response Format

```json
{
  "date": "2025-01-15",
  "quote": "You have power over your mind - not outside events...",
  "attribution": "Marcus Aurelius, Meditations, Book 5",
  "theme": "Self-Mastery",
  "reflection": "In our modern world...",
  "monthlyTheme": {
    "name": "Discipline and Self-Improvement",
    "description": "Focus on building habits, self-control, and starting fresh"
  }
}
```

### Features

- Public access (no authentication required)
- CORS enabled for web/hardware device access
- Rate limiting: 10 burst, 5 req/sec (more than sufficient for <100 calls/day)
- Fast response times (~100ms) - reads from pre-generated cache
- Negligible cost (~$0.00-$0.01/month at low volume)

For complete API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

For API deployment instructions, see [API_DEPLOYMENT_GUIDE.md](API_DEPLOYMENT_GUIDE.md).

## Setup and Deployment

For complete deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

For ongoing maintenance and updates, see [MAINTENANCE.md](MAINTENANCE.md).

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

See [MAINTENANCE.md](MAINTENANCE.md) for:
- Adding/removing recipients
- Updating Lambda code
- Changing delivery schedule
- Monitoring and troubleshooting
- Cost management

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

- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
- [API_DEPLOYMENT_GUIDE.md](API_DEPLOYMENT_GUIDE.md) - API deployment guide
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference and usage
- [MAINTENANCE.md](MAINTENANCE.md) - Ongoing maintenance and operations
- [prd.md](prd.md) - Product requirements
- [projectplan.md](projectplan.md) - Implementation plan

## License

Personal project by James Mooney