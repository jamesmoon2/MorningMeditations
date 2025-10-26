"""
Quote Loader Module

Loads daily quotes from the pre-drafted 365-day quote database.
Maps calendar dates to specific quotes from stoic_quotes_365_days.json.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class QuoteLoader:
    """Loads daily quotes from the 365-day quote database."""

    def __init__(self, bucket_name: str):
        """
        Initialize the QuoteLoader.

        Args:
            bucket_name: S3 bucket containing the quotes database
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3')
        self._quotes_cache: Optional[Dict[str, Any]] = None

    def load_quotes_database(self) -> Dict[str, Any]:
        """
        Load the complete 365-day quotes database from S3.

        Returns:
            Dictionary with monthly quote data

        Raises:
            Exception: If the database cannot be loaded
        """
        if self._quotes_cache is not None:
            return self._quotes_cache

        try:
            logger.info(f"Loading quotes database from s3://{self.bucket_name}/config/stoic_quotes_365_days.json")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key='config/stoic_quotes_365_days.json'
            )

            quotes_data = json.loads(response['Body'].read().decode('utf-8'))
            self._quotes_cache = quotes_data
            logger.info("Successfully loaded quotes database")
            return quotes_data

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error("Quotes database not found in S3")
                raise Exception("stoic_quotes_365_days.json not found in S3 bucket")
            else:
                logger.error(f"Error loading quotes database: {str(e)}")
                raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in quotes database: {str(e)}")
            raise Exception("Quotes database contains invalid JSON")

    def get_quote_for_date(self, date: datetime) -> Dict[str, str]:
        """
        Get the appropriate quote for a specific date.

        Args:
            date: The date to get a quote for

        Returns:
            Dictionary with keys:
                - quote: The stoic quote text
                - attribution: Who said it and source
                - theme: The monthly theme

        Raises:
            Exception: If quote cannot be found for the given date
        """
        quotes_db = self.load_quotes_database()

        # Get month name (lowercase)
        month_name = date.strftime('%B').lower()
        day_num = date.day

        # Handle leap year: Feb 29 -> use Feb 28
        if month_name == 'february' and day_num == 29:
            logger.info("Leap year detected: Using February 28 quote for February 29")
            day_num = 28

        # Validate month exists
        if month_name not in quotes_db:
            raise Exception(f"Month '{month_name}' not found in quotes database")

        month_quotes = quotes_db[month_name]

        # Find quote for this day
        for quote_entry in month_quotes:
            if quote_entry['day'] == day_num:
                logger.info(f"Found quote for {month_name.title()} {day_num}")
                return {
                    'quote': quote_entry['quote'],
                    'attribution': quote_entry['attribution'],
                    'theme': quote_entry['theme']
                }

        # If we get here, the day wasn't found
        raise Exception(f"No quote found for {month_name.title()} {day_num}")

    def validate_database_completeness(self) -> Dict[str, Any]:
        """
        Validate that the quotes database contains all 365 days.

        Returns:
            Dictionary with validation results:
                - complete: Boolean indicating if all days are present
                - total_quotes: Total number of quotes found
                - missing_days: List of missing (month, day) tuples
                - duplicate_days: List of duplicate (month, day) tuples
        """
        quotes_db = self.load_quotes_database()

        expected_days = {
            'january': 31,
            'february': 28,  # Non-leap year
            'march': 31,
            'april': 30,
            'may': 31,
            'june': 30,
            'july': 31,
            'august': 31,
            'september': 30,
            'october': 31,
            'november': 30,
            'december': 31
        }

        total_quotes = 0
        missing_days = []
        duplicate_days = []

        for month, expected_count in expected_days.items():
            if month not in quotes_db:
                missing_days.extend([(month, day) for day in range(1, expected_count + 1)])
                continue

            month_quotes = quotes_db[month]
            total_quotes += len(month_quotes)

            # Check for all days present
            days_found = set()
            for quote_entry in month_quotes:
                day = quote_entry.get('day')
                if day in days_found:
                    duplicate_days.append((month, day))
                days_found.add(day)

            # Find missing days
            for day in range(1, expected_count + 1):
                if day not in days_found:
                    missing_days.append((month, day))

        is_complete = len(missing_days) == 0 and len(duplicate_days) == 0 and total_quotes == 365

        validation_result = {
            'complete': is_complete,
            'total_quotes': total_quotes,
            'expected_quotes': 365,
            'missing_days': missing_days,
            'duplicate_days': duplicate_days
        }

        if is_complete:
            logger.info("Quotes database validation: COMPLETE (365/365 quotes)")
        else:
            logger.warning(
                f"Quotes database validation: INCOMPLETE "
                f"({total_quotes}/365 quotes, "
                f"{len(missing_days)} missing, "
                f"{len(duplicate_days)} duplicates)"
            )

        return validation_result


def get_quote_for_date(bucket_name: str, date: datetime) -> Dict[str, str]:
    """
    Convenience function to get a quote for a specific date.

    Args:
        bucket_name: S3 bucket containing the quotes database
        date: The date to get a quote for

    Returns:
        Dictionary with quote, attribution, and theme
    """
    loader = QuoteLoader(bucket_name)
    return loader.get_quote_for_date(date)
