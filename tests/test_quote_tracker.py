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

        quote = "You have power over your mind - not outside events."
        attribution = "Marcus Aurelius - Meditations 6.8"
        reflection = "This is a test reflection about the power of the mind and how we can control our thoughts and reactions to external events."
        theme = "Mortality and Impermanence"

        updated = tracker.add_quote(
            history, "2025-10-22", quote, attribution, reflection, theme
        )

        assert len(updated["quotes"]) == 1
        assert updated["quotes"][0]["date"] == "2025-10-22"
        assert updated["quotes"][0]["quote"] == quote
        assert updated["quotes"][0]["attribution"] == attribution
        assert updated["quotes"][0]["reflection"] == reflection
        assert updated["quotes"][0]["theme"] == theme

    def test_get_current_month_quotes(self):
        """Test getting quotes from current month."""
        today = datetime.now()
        this_month = today.replace(day=5)
        last_month = today - timedelta(days=35)

        quote1 = "You have power over your mind - not outside events."
        quote2 = "The impediment to action advances action."
        reflection1 = "Test reflection about power of mind."
        reflection2 = "Test reflection about obstacles."

        history = {
            "quotes": [
                {
                    "date": this_month.strftime("%Y-%m-%d"),
                    "quote": quote1,
                    "attribution": "Marcus Aurelius - Meditations 6.8",
                    "reflection": reflection1,
                    "theme": "Test",
                },
                {
                    "date": last_month.strftime("%Y-%m-%d"),
                    "quote": quote2,
                    "attribution": "Marcus Aurelius - Meditations 5.20",
                    "reflection": reflection2,
                    "theme": "Test",
                },
            ]
        }

        tracker = QuoteTracker("test-bucket")
        current_month = tracker.get_current_month_quotes(history, today)

        # Should only get quotes from this month
        assert len(current_month) == 1
        assert current_month[0]["quote"] == quote1
        assert current_month[0]["reflection"] == reflection1

    def test_get_current_month_quotes_empty_history(self):
        """Test getting current month quotes from empty history."""
        history = {"quotes": []}
        tracker = QuoteTracker("test-bucket")
        today = datetime.now()

        current_month = tracker.get_current_month_quotes(history, today)

        assert len(current_month) == 0

    def test_get_quote_count(self):
        """Test getting quote count."""
        history = {
            "quotes": [
                {"date": "2025-01-01", "attribution": "Test 1", "theme": "Test"},
                {"date": "2025-01-02", "attribution": "Test 2", "theme": "Test"},
                {"date": "2025-01-03", "attribution": "Test 3", "theme": "Test"},
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
                    "theme": "Test",
                },
                {
                    "date": recent_date.strftime("%Y-%m-%d"),
                    "attribution": "Recent Quote",
                    "theme": "Test",
                },
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
                    "theme": "Test",
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

        quote = "Test quote text"
        attribution = "Test Attribution"
        reflection = "Test reflection text"
        theme = "Test Theme"

        updated = tracker.add_quote(
            history, "2025-10-22", quote, attribution, reflection, theme
        )

        assert "quotes" in updated
        assert len(updated["quotes"]) == 1
