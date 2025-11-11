# Morning Reflections API Documentation

## Overview

The Morning Reflections API provides read-only access to daily stoic reflections that are generated and emailed each morning. This API is designed for hardware devices and applications that want to display the daily reflection.

## Base URL

After deployment, your API will be available at:
```
https://{api-id}.execute-api.{region}.amazonaws.com/prod/
```

The exact URL will be provided in the CloudFormation outputs after deployment.

## Endpoints

### 1. Get Today's Reflection

Retrieves the reflection generated for today.

**Endpoint:** `GET /reflection/today`

**Example Request:**
```bash
curl https://{api-url}/reflection/today
```

**Example Response (200 OK):**
```json
{
  "date": "2025-01-15",
  "quote": "You have power over your mind - not outside events. Realize this, and you will find strength.",
  "attribution": "Marcus Aurelius, Meditations, Book 5",
  "theme": "Self-Mastery",
  "reflection": "In our modern world of constant notifications and external demands, Marcus Aurelius reminds us of a profound truth...",
  "monthlyTheme": {
    "name": "Discipline and Self-Improvement",
    "description": "Focus on building habits, self-control, and starting fresh"
  }
}
```

### 2. Get Reflection by Date

Retrieves the reflection for a specific date.

**Endpoint:** `GET /reflection/{date}`

**Path Parameters:**
- `date` (string, required): Date in YYYY-MM-DD format

**Example Request:**
```bash
curl https://{api-url}/reflection/2025-01-10
```

**Example Response (200 OK):**
```json
{
  "date": "2025-01-10",
  "quote": "Waste no more time arguing what a good man should be. Be One.",
  "attribution": "Marcus Aurelius, Meditations",
  "theme": "Action",
  "reflection": "Marcus Aurelius cuts through all philosophical debate with this simple command...",
  "monthlyTheme": {
    "name": "Discipline and Self-Improvement",
    "description": "Focus on building habits, self-control, and starting fresh"
  }
}
```

## Error Responses

### 404 Not Found

Returned when no reflection exists for the requested date.

```json
{
  "error": "Reflection not found for date: 2025-12-31",
  "date": "2025-12-31"
}
```

### 400 Bad Request

Returned when the date format is invalid.

```json
{
  "error": "Invalid date format: 2025/01/15. Expected YYYY-MM-DD"
}
```

### 500 Internal Server Error

Returned when an unexpected error occurs.

```json
{
  "error": "Internal server error",
  "message": "Error details..."
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | ISO date (YYYY-MM-DD) of the reflection |
| `quote` | string | The stoic quote for the day |
| `attribution` | string | Source of the quote (author and work) |
| `theme` | string | Daily theme associated with the quote |
| `reflection` | string | AI-generated reflection (200-250 words) |
| `monthlyTheme.name` | string | Name of the month's overarching theme |
| `monthlyTheme.description` | string | Description of the monthly theme |

## Rate Limiting

The API is configured with the following limits:
- **Burst**: 10 concurrent requests
- **Rate**: 5 requests per second

These limits are enforced at the API Gateway level and should be sufficient for hardware device usage (<100 requests/day).

## CORS

The API supports Cross-Origin Resource Sharing (CORS) with the following configuration:
- **Allowed Origins**: `*` (all origins)
- **Allowed Methods**: `GET`, `OPTIONS`
- **Allowed Headers**: `Content-Type`, `X-Amz-Date`, `Authorization`, `X-Api-Key`

## Data Availability

Reflections are available for:
- **Current date**: Available after 6 AM PST daily
- **Historical dates**: Up to 400 days in the past

## Authentication

The API is currently **public** and does not require authentication or API keys. Rate limiting is used to prevent abuse.

## Example Hardware Device Integration

Here's a simple example of how a hardware device might fetch today's reflection:

```python
import requests
import json

API_URL = "https://{api-id}.execute-api.{region}.amazonaws.com/prod"

def get_todays_reflection():
    try:
        response = requests.get(f"{API_URL}/reflection/today")
        response.raise_for_status()

        data = response.json()

        # Display on device
        print(f"Date: {data['date']}")
        print(f"Quote: {data['quote']}")
        print(f"- {data['attribution']}")
        print(f"\n{data['reflection']}")

        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching reflection: {e}")
        return None

# Fetch and display
get_todays_reflection()
```

## Support

For issues or questions, please refer to the project repository.

## Cost Estimate

With <100 API calls per day:
- **API Gateway**: Free tier covers first 1M requests/month
- **Lambda**: ~$0.20 per million requests (very fast execution)
- **S3**: Negligible (already storing data)
- **Total**: Essentially $0/month at this volume
