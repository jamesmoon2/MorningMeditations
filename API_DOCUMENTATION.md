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

## Code Examples

### Python

```python
import requests
from datetime import datetime
import time

API_URL = "https://{api-id}.execute-api.{region}.amazonaws.com/prod"

def get_todays_reflection():
    """Fetch today's reflection with error handling and retries."""
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{API_URL}/reflection/today",
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Display on device
            print(f"Date: {data['date']}")
            print(f"Monthly Theme: {data['monthlyTheme']['name']}")
            print(f"\n{data['quote']}")
            print(f"- {data['attribution']}")
            print(f"\n{data['reflection']}")

            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"No reflection available for today yet (6 AM PST)")
                return None
            elif e.response.status_code == 429:
                print(f"Rate limited. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"HTTP error: {e}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

    print("Failed after maximum retries")
    return None

def get_reflection_by_date(date_str):
    """Fetch reflection for a specific date (YYYY-MM-DD)."""
    try:
        response = requests.get(
            f"{API_URL}/reflection/{date_str}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Usage
if __name__ == "__main__":
    # Get today's reflection
    reflection = get_todays_reflection()

    # Get specific date
    past_reflection = get_reflection_by_date("2025-01-10")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_URL = 'https://{api-id}.execute-api.{region}.amazonaws.com/prod';

async function getTodaysReflection() {
  try {
    const response = await axios.get(`${API_URL}/reflection/today`, {
      timeout: 10000,
      headers: {
        'Accept': 'application/json'
      }
    });

    const data = response.data;

    console.log(`Date: ${data.date}`);
    console.log(`Monthly Theme: ${data.monthlyTheme.name}`);
    console.log(`\n${data.quote}`);
    console.log(`- ${data.attribution}`);
    console.log(`\n${data.reflection}`);

    return data;

  } catch (error) {
    if (error.response) {
      // Server responded with error status
      console.error(`Error ${error.response.status}: ${error.response.data.error}`);
    } else if (error.request) {
      // Request made but no response
      console.error('No response from server');
    } else {
      // Request setup error
      console.error('Error:', error.message);
    }
    return null;
  }
}

async function getReflectionByDate(dateStr) {
  try {
    const response = await axios.get(`${API_URL}/reflection/${dateStr}`, {
      timeout: 10000
    });
    return response.data;
  } catch (error) {
    console.error('Error:', error.message);
    return null;
  }
}

// Usage
getTodaysReflection();
```

### JavaScript (Browser/Fetch API)

```javascript
const API_URL = 'https://{api-id}.execute-api.{region}.amazonaws.com/prod';

async function getTodaysReflection() {
  try {
    const response = await fetch(`${API_URL}/reflection/today`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    const data = await response.json();

    // Update UI
    document.getElementById('date').textContent = data.date;
    document.getElementById('theme').textContent = data.monthlyTheme.name;
    document.getElementById('quote').textContent = data.quote;
    document.getElementById('attribution').textContent = data.attribution;
    document.getElementById('reflection').textContent = data.reflection;

    return data;

  } catch (error) {
    console.error('Failed to fetch reflection:', error);
    document.getElementById('error').textContent = error.message;
    return null;
  }
}

// Call on page load
getTodaysReflection();
```

### cURL

```bash
# Get today's reflection
curl -X GET "https://{api-id}.execute-api.{region}.amazonaws.com/prod/reflection/today" \
  -H "Accept: application/json"

# Get specific date
curl -X GET "https://{api-id}.execute-api.{region}.amazonaws.com/prod/reflection/2025-01-10" \
  -H "Accept: application/json"

# Pretty print with jq
curl -s "https://{api-id}.execute-api.{region}.amazonaws.com/prod/reflection/today" | jq '.'

# Extract just the quote
curl -s "https://{api-id}.execute-api.{region}.amazonaws.com/prod/reflection/today" | jq -r '.quote'
```

### Arduino/ESP32 (C++)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* API_URL = "https://{api-id}.execute-api.{region}.amazonaws.com/prod";

void getTodaysReflection() {
  HTTPClient http;

  String endpoint = String(API_URL) + "/reflection/today";
  http.begin(endpoint);
  http.addHeader("Accept", "application/json");

  int httpCode = http.GET();

  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();

    // Parse JSON
    DynamicJsonDocument doc(4096);
    deserializeJson(doc, payload);

    const char* date = doc["date"];
    const char* quote = doc["quote"];
    const char* attribution = doc["attribution"];
    const char* reflection = doc["reflection"];

    // Display on screen
    Serial.println(date);
    Serial.println(quote);
    Serial.println(attribution);
    Serial.println(reflection);

  } else {
    Serial.printf("HTTP Error: %d\n", httpCode);
  }

  http.end();
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  getTodaysReflection();
}

void loop() {
  // Fetch once per day at startup
  delay(60000);
}
```

## Best Practices

### 1. Caching

The API serves pre-generated reflections that don't change throughout the day. Implement client-side caching to reduce API calls:

```python
import requests
from datetime import datetime, timedelta
import json
import os

CACHE_FILE = 'reflection_cache.json'
CACHE_DURATION_HOURS = 24

def get_cached_reflection():
    """Get reflection from cache if available and fresh."""
    if not os.path.exists(CACHE_FILE):
        return None

    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)

    cached_date = cache.get('date')
    if cached_date == datetime.now().strftime('%Y-%m-%d'):
        return cache

    return None

def save_to_cache(reflection):
    """Save reflection to local cache."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(reflection, f)

def get_todays_reflection_with_cache():
    """Get today's reflection, using cache when possible."""
    cached = get_cached_reflection()
    if cached:
        print("Using cached reflection")
        return cached

    # Fetch from API
    reflection = get_todays_reflection()
    if reflection:
        save_to_cache(reflection)

    return reflection
```

**Recommendation**: Cache today's reflection and only fetch once per day.

### 2. Error Handling

Always implement robust error handling:

- **404 errors**: Reflection not available yet (before 6 AM PST) or future date requested
- **429 errors**: Rate limit exceeded - implement exponential backoff
- **500 errors**: Server error - retry with backoff
- **Network errors**: Implement retry logic with timeouts

### 3. Fetch Timing

For optimal reliability:
- Fetch **after 6:30 AM PST** (14:30 UTC) to ensure the daily reflection is generated
- Implement a daily scheduled fetch rather than on-demand requests
- For hardware devices, fetch once at startup and cache for the day

### 4. Response Validation

Always validate the response structure:

```python
def validate_reflection(data):
    """Validate reflection response has required fields."""
    required_fields = ['date', 'quote', 'attribution', 'theme', 'reflection', 'monthlyTheme']

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    if 'name' not in data['monthlyTheme'] or 'description' not in data['monthlyTheme']:
        raise ValueError("Invalid monthlyTheme structure")

    return True
```

### 5. Rate Limiting Compliance

Respect the API rate limits:
- Maximum 5 requests per second
- Maximum 10 concurrent requests
- Implement exponential backoff on 429 responses
- Don't make unnecessary requests - use caching

### 6. Timeout Configuration

Set appropriate timeouts:
- **Connection timeout**: 5 seconds
- **Read timeout**: 10 seconds
- Total recommended timeout: 15 seconds

## Common Use Cases

### Use Case 1: Daily Quote Display (E-Ink Device)

```python
import requests
from PIL import Image, ImageDraw, ImageFont

def display_on_eink(reflection):
    """Display reflection on e-ink screen."""
    # Create image
    img = Image.new('L', (800, 600), 255)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)

    # Draw content
    y_position = 50
    draw.text((50, y_position), reflection['monthlyTheme']['name'], font=font_small, fill=0)

    y_position += 80
    # Wrap quote text
    wrapped_quote = wrap_text(reflection['quote'], 60)
    for line in wrapped_quote:
        draw.text((50, y_position), line, font=font_large, fill=0)
        y_position += 30

    y_position += 20
    draw.text((50, y_position), f"- {reflection['attribution']}", font=font_medium, fill=0)

    # Display on e-ink
    epd.display(epd.getbuffer(img))

# Fetch once per day at 7 AM PST
reflection = get_todays_reflection_with_cache()
if reflection:
    display_on_eink(reflection)
```

### Use Case 2: Mobile App Daily Notification

```javascript
// React Native example
import PushNotification from 'react-native-push-notification';
import AsyncStorage from '@react-native-async-storage/async-storage';

async function scheduleDailyReflection() {
  const API_URL = 'https://{api-url}';

  try {
    // Check if already fetched today
    const lastFetch = await AsyncStorage.getItem('lastFetchDate');
    const today = new Date().toISOString().split('T')[0];

    if (lastFetch === today) {
      console.log('Already fetched today');
      return;
    }

    // Fetch reflection
    const response = await fetch(`${API_URL}/reflection/today`);
    const data = await response.json();

    // Save to storage
    await AsyncStorage.setItem('lastFetchDate', today);
    await AsyncStorage.setItem('todaysReflection', JSON.stringify(data));

    // Send notification
    PushNotification.localNotification({
      title: 'Morning Reflection',
      message: data.quote,
      bigText: data.reflection,
      channelId: 'daily-reflection',
    });

  } catch (error) {
    console.error('Failed to fetch reflection:', error);
  }
}

// Schedule for 7 AM daily
```

### Use Case 3: Web Widget

```html
<!DOCTYPE html>
<html>
<head>
  <title>Daily Stoic Reflection</title>
  <style>
    .reflection-widget {
      max-width: 600px;
      margin: 20px auto;
      padding: 20px;
      border: 1px solid #ddd;
      border-radius: 8px;
      font-family: Georgia, serif;
    }
    .quote {
      font-size: 20px;
      font-style: italic;
      margin: 20px 0;
    }
    .attribution {
      text-align: right;
      color: #666;
    }
    .reflection {
      margin-top: 20px;
      line-height: 1.6;
    }
  </style>
</head>
<body>
  <div class="reflection-widget">
    <div id="theme"></div>
    <div class="quote" id="quote"></div>
    <div class="attribution" id="attribution"></div>
    <div class="reflection" id="reflection"></div>
  </div>

  <script>
    async function loadReflection() {
      const API_URL = 'https://{api-url}';

      try {
        const response = await fetch(`${API_URL}/reflection/today`);
        const data = await response.json();

        document.getElementById('theme').textContent = data.monthlyTheme.name;
        document.getElementById('quote').textContent = `"${data.quote}"`;
        document.getElementById('attribution').textContent = `— ${data.attribution}`;
        document.getElementById('reflection').textContent = data.reflection;
      } catch (error) {
        console.error('Failed to load reflection:', error);
      }
    }

    loadReflection();
  </script>
</body>
</html>
```

## Performance Considerations

### Response Times

- **Typical response time**: 100-200ms
- **Cold start (first request)**: 1-2 seconds
- **Subsequent requests**: 50-150ms

### Response Size

- **Typical response**: 1-2 KB (uncompressed)
- **With reflection text**: 2-3 KB
- Enable gzip compression in your HTTP client for smaller transfers

### Bandwidth Usage

At <100 requests/day with caching:
- **Daily bandwidth**: ~0.2 MB
- **Monthly bandwidth**: ~6 MB
- Minimal data usage suitable for IoT devices

## Troubleshooting

### Problem: 404 Error for Today's Date

**Cause**: Reflection not generated yet (before 6 AM PST)

**Solution**:
- Wait until after 6:30 AM PST
- Implement fallback to yesterday's reflection
- Show cached reflection from previous day

```python
def get_reflection_with_fallback():
    """Try today, fallback to yesterday."""
    reflection = get_reflection_by_date(datetime.now().strftime('%Y-%m-%d'))

    if not reflection:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        reflection = get_reflection_by_date(yesterday)

    return reflection
```

### Problem: Rate Limit Exceeded (429)

**Cause**: More than 5 requests per second or 10 concurrent requests

**Solution**:
- Implement caching to reduce requests
- Add exponential backoff
- Avoid polling - fetch once per day

### Problem: Slow Response Times

**Cause**: Lambda cold start or network latency

**Solution**:
- Accept 1-2 second cold starts
- Implement timeout handling
- Cache aggressively
- Make requests asynchronously in the background

### Problem: CORS Errors in Browser

**Cause**: Browser blocking cross-origin requests

**Solution**: The API already has CORS enabled. Ensure you're:
- Using HTTPS
- Not modifying headers unnecessarily
- Using standard content types

## API Versioning

- **Current Version**: 1.0
- **Version Strategy**: URL-based versioning will be used for breaking changes
- **Breaking Changes**: Will be announced with 30 days notice
- **Deprecation**: Old versions will be supported for 90 days after new version release

## Data Freshness

- **Update Schedule**: Daily at 6:00 AM PST (14:00 UTC)
- **Historical Data**: Available for up to 400 days
- **Future Dates**: Not available (404 error)
- **Consistency**: Same reflection returned throughout the day

## Support

For issues or questions:
- Review this documentation
- Check the troubleshooting section
- Refer to the project repository

## Cost Estimate

With <100 API calls per day:
- **API Gateway**: Free tier covers first 1M requests/month
- **Lambda**: ~$0.20 per million requests (very fast execution)
- **S3**: Negligible (already storing data)
- **Total**: Essentially $0/month at this volume

## Changelog

### Version 1.0 (2025-11-12)
- Initial release
- Two endpoints: `/reflection/today` and `/reflection/{date}`
- Public access with rate limiting
- CORS enabled
- Response includes quote, attribution, theme, reflection, and monthly theme
