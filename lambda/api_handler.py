"""
API Lambda handler for serving morning reflections.

This handler provides a read-only API to access pre-generated daily reflections
from the quote history stored in S3.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from quote_tracker import QuoteTracker
from themes import get_monthly_theme

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an API Gateway response with CORS headers.

    Args:
        status_code: HTTP status code
        body: Response body dictionary

    Returns:
        API Gateway response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body)
    }


def find_reflection_by_date(
    history: Dict[str, Any],
    target_date: str
) -> Optional[Dict[str, Any]]:
    """
    Find a reflection entry by date in the history.

    Args:
        history: Quote history dictionary from S3
        target_date: ISO format date string (YYYY-MM-DD)

    Returns:
        Quote entry dictionary if found, None otherwise
    """
    for quote_entry in history.get('quotes', []):
        if quote_entry.get('date') == target_date:
            return quote_entry
    return None


def format_reflection_response(quote_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a quote entry into the API response format.

    Args:
        quote_entry: Quote entry from history

    Returns:
        Formatted response dictionary
    """
    # Extract date and get monthly theme
    date_str = quote_entry['date']
    date_obj = datetime.fromisoformat(date_str)
    monthly_theme = get_monthly_theme(date_obj.month)

    return {
        'date': date_str,
        'quote': quote_entry['quote'],
        'attribution': quote_entry['attribution'],
        'theme': quote_entry['theme'],
        'reflection': quote_entry['reflection'],
        'monthlyTheme': {
            'name': monthly_theme['name'],
            'description': monthly_theme['description']
        }
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for the Morning Reflections API.

    Supports:
    - GET /reflection/today - Returns today's reflection
    - GET /reflection/{date} - Returns reflection for specific date (YYYY-MM-DD)
    - OPTIONS - CORS preflight

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log the incoming request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        logger.info(f"Received {http_method} request to {path}")

        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})

        # Validate environment variables
        bucket_name = os.environ.get('BUCKET_NAME')
        if not bucket_name:
            logger.error("BUCKET_NAME environment variable not set")
            return create_response(500, {
                'error': 'Server configuration error'
            })

        # Initialize tracker and load history
        tracker = QuoteTracker(bucket_name)
        history = tracker.load_history()

        logger.info(f"Loaded history with {len(history.get('quotes', []))} quotes")

        # Parse the path to determine the requested date
        path_parts = path.strip('/').split('/')

        # Determine target date
        target_date = None

        if len(path_parts) >= 2:
            if path_parts[1] == 'today':
                # /reflection/today
                target_date = datetime.now().strftime('%Y-%m-%d')
            else:
                # /reflection/{date}
                target_date = path_parts[1]

                # Validate date format
                try:
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return create_response(400, {
                        'error': f'Invalid date format: {target_date}. Expected YYYY-MM-DD'
                    })
        else:
            return create_response(400, {
                'error': 'Invalid path. Use /reflection/today or /reflection/YYYY-MM-DD'
            })

        # Find the reflection
        quote_entry = find_reflection_by_date(history, target_date)

        if quote_entry is None:
            logger.info(f"No reflection found for date: {target_date}")
            return create_response(404, {
                'error': f'Reflection not found for date: {target_date}',
                'date': target_date
            })

        # Format and return the response
        response_body = format_reflection_response(quote_entry)
        logger.info(f"Successfully retrieved reflection for {target_date}")

        return create_response(200, response_body)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })
