"""
Quote history archival functionality.

Manages quote history in S3 for posterity, tracking daily quotes and reflections.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class QuoteTracker:
    """Manages quote history in S3 for archival purposes."""

    def __init__(self, bucket_name: str, history_key: str = "quote_history.json"):
        """
        Initialize the QuoteTracker.

        Args:
            bucket_name: Name of the S3 bucket
            history_key: S3 key for the history file (default: quote_history.json)
        """
        self.bucket_name = bucket_name
        self.history_key = history_key
        self.s3_client = boto3.client('s3')

    def load_history(self) -> Dict[str, Any]:
        """
        Load quote history from S3.

        Returns:
            Dictionary with 'quotes' list containing quote history

        Raises:
            Exception: If S3 read fails (except for missing file)
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.history_key
            )
            content = response['Body'].read().decode('utf-8')
            history = json.loads(content)
            logger.info(f"Loaded history with {len(history.get('quotes', []))} quotes")
            return history

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                # File doesn't exist yet, return empty history
                logger.info("No existing history file found, starting fresh")
                return {"quotes": []}
            else:
                logger.error(f"Error loading history from S3: {e}")
                raise

    def save_history(self, history: Dict[str, Any]) -> None:
        """
        Save quote history to S3.

        Args:
            history: Dictionary with 'quotes' list to save

        Raises:
            Exception: If S3 write fails
        """
        try:
            content = json.dumps(history, indent=2)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.history_key,
                Body=content.encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Saved history with {len(history.get('quotes', []))} quotes")

        except ClientError as e:
            logger.error(f"Error saving history to S3: {e}")
            raise

    def add_quote(
        self,
        history: Dict[str, Any],
        date: str,
        quote: str,
        attribution: str,
        reflection: str,
        theme: str
    ) -> Dict[str, Any]:
        """
        Add a new quote and reflection to the history for archival purposes.

        Args:
            history: Existing quote history dictionary
            date: ISO format date string (YYYY-MM-DD)
            quote: The stoic quote text
            attribution: Quote attribution (e.g., "Marcus Aurelius - Meditations 4.3")
            reflection: The full reflection text
            theme: Monthly theme name

        Returns:
            Updated history dictionary
        """
        if 'quotes' not in history:
            history['quotes'] = []

        new_entry = {
            "date": date,
            "quote": quote,
            "attribution": attribution,
            "theme": theme,
            "reflection": reflection
        }

        history['quotes'].append(new_entry)
        logger.info(f"Added entry to history: {attribution} on {date}")

        return history

    def get_quote_count(self, history: Dict[str, Any]) -> int:
        """
        Get total number of quotes in history.

        Args:
            history: Quote history dictionary

        Returns:
            Number of quotes in history
        """
        return len(history.get('quotes', []))

    def get_current_month_quotes(
        self,
        history: Dict[str, Any],
        current_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get all quotes from the current month and year.

        Args:
            history: Quote history dictionary
            current_date: Current date to determine month and year

        Returns:
            List of quote entries from the current month
        """
        current_month = current_date.month
        current_year = current_date.year

        filtered_quotes = []
        for quote_entry in history.get('quotes', []):
            try:
                quote_date = datetime.fromisoformat(quote_entry['date'])
                if quote_date.month == current_month and quote_date.year == current_year:
                    # Only include quotes from before the current date
                    if quote_date < current_date:
                        filtered_quotes.append(quote_entry)
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid quote entry: {e}")
                continue

        logger.info(f"Found {len(filtered_quotes)} quotes from current month")
        return filtered_quotes

    def cleanup_old_quotes(
        self,
        history: Dict[str, Any],
        keep_days: int = 400
    ) -> Dict[str, Any]:
        """
        Remove quotes older than specified days to keep file size manageable.
        Keeps a buffer beyond the 365-day repeat window.

        Args:
            history: Quote history dictionary
            keep_days: Number of days of history to keep (default: 400)

        Returns:
            Updated history dictionary with old quotes removed
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        original_count = len(history.get('quotes', []))

        filtered_quotes = []
        for quote_entry in history.get('quotes', []):
            try:
                quote_date = datetime.fromisoformat(quote_entry['date'])
                if quote_date >= cutoff_date:
                    filtered_quotes.append(quote_entry)
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid quote entry during cleanup: {e}")
                continue

        history['quotes'] = filtered_quotes
        removed_count = original_count - len(filtered_quotes)

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old quotes from history")

        return history
