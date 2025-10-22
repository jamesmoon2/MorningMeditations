"""Unit tests for quote_tracker module."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent / "lambda"
sys.path.insert(0, str(lambda_dir))

from quote_tracker import QuoteTracker


class TestQuoteTracker:
    """Test cases for quote tracking functionality."""

    def test_add_quote(self):
        """Test adding a quote to history."""
        history = {"quotes": []}
        tracker = QuoteTracker("test-bucket")

        updated = tracker.add_quote(
            history,
            "2025-10-22",
            "Marcus Aurelius - Meditations 4.3",
            "Mortality and Impermanence"
        )

        assert len(updated["quotes"]) == 1
        assert updated["quotes"][0]["date"] == "2025-10-22"
        assert updated["quotes"][0]["attribution"] == "Marcus Aurelius - Meditations 4.3"
        assert updated["quotes"][0]["theme"] == "Mortality and Impermanence"

    def test_get_used_quotes_within_range(self):
        """Test getting quotes used within date range."""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        last_year = today - timedelta(days=400)

        history = {
            "quotes": [
                {
                    "date": yesterday.strftime("%Y-%m-%d"),
                    "attribution": "Marcus Aurelius - Meditations 2.1",
                    "theme": "Test"
                },
                {
                    "date": last_year.strftime("%Y-%m-%d"),
                    "attribution": "Epictetus - Enchiridion 1",
                    "theme": "Test"
                }
            ]
        }

        tracker = QuoteTracker("test-bucket")
        used = tracker.get_used_quotes(history, days=365)

        # Should only get the recent quote, not the old one
        assert len(used) == 1
        assert "Marcus Aurelius - Meditations 2.1" in used
        assert "Epictetus - Enchiridion 1" not in used

    def test_get_used_quotes_empty_history(self):
        """Test getting used quotes from empty history."""
        history = {"quotes": []}
        tracker = QuoteTracker("test-bucket")

        used = tracker.get_used_quotes(history, days=365)

        assert len(used) == 0

    def test_get_quote_count(self):
        """Test getting quote count."""
        history = {
            "quotes": [
                {"date": "2025-01-01", "attribution": "Test 1", "theme": "Test"},
                {"date": "2025-01-02", "attribution": "Test 2", "theme": "Test"},
                {"date": "2025-01-03", "attribution": "Test 3", "theme": "Test"}
            ]
        }

        tracker = QuoteTracker("test-bucket")
        count = tracker.get_quote_count(history)

        assert count == 3

    def test_cleanup_old_quotes(self):
        """Test cleanup of old quotes."""
        today = datetime.now()
        old_date = today - timedelta(days=500)
        recent_date = today - timedelta(days=100)

        history = {
            "quotes": [
                {
                    "date": old_date.strftime("%Y-%m-%d"),
                    "attribution": "Old Quote",
                    "theme": "Test"
                },
                {
                    "date": recent_date.strftime("%Y-%m-%d"),
                    "attribution": "Recent Quote",
                    "theme": "Test"
                }
            ]
        }

        tracker = QuoteTracker("test-bucket")
        cleaned = tracker.cleanup_old_quotes(history, keep_days=400)

        # Should only keep the recent quote
        assert len(cleaned["quotes"]) == 1
        assert cleaned["quotes"][0]["attribution"] == "Recent Quote"

    def test_cleanup_old_quotes_empty(self):
        """Test cleanup with no quotes to remove."""
        today = datetime.now()
        recent_date = today - timedelta(days=10)

        history = {
            "quotes": [
                {
                    "date": recent_date.strftime("%Y-%m-%d"),
                    "attribution": "Recent Quote",
                    "theme": "Test"
                }
            ]
        }

        tracker = QuoteTracker("test-bucket")
        cleaned = tracker.cleanup_old_quotes(history, keep_days=400)

        # Should keep the quote
        assert len(cleaned["quotes"]) == 1

    def test_add_quote_to_empty_history(self):
        """Test adding a quote when history doesn't have 'quotes' key."""
        history = {}
        tracker = QuoteTracker("test-bucket")

        updated = tracker.add_quote(
            history,
            "2025-10-22",
            "Test Attribution",
            "Test Theme"
        )

        assert "quotes" in updated
        assert len(updated["quotes"]) == 1
