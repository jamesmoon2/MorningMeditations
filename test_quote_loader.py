#!/usr/bin/env python3
"""
Test the quote loader functionality.

Tests that quotes can be loaded for different dates.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def test_quote_loader():
    """Test the quote loader with various dates."""
    # Load the quotes database
    quotes_file = Path(__file__).parent / 'config' / 'stoic_quotes_365_days.json'

    with open(quotes_file, 'r') as f:
        quotes_db = json.load(f)

    # Test dates
    test_dates = [
        datetime(2025, 1, 1),   # January 1
        datetime(2025, 2, 14),  # February 14 (Valentine's Day)
        datetime(2024, 2, 29),  # Leap year (should use Feb 28)
        datetime(2025, 6, 15),  # June 15
        datetime(2025, 10, 26), # October 26 (today)
        datetime(2025, 12, 31), # December 31
    ]

    print("Testing quote loader...")
    print()

    all_passed = True

    for test_date in test_dates:
        month_name = test_date.strftime('%B').lower()
        day_num = test_date.day

        # Handle leap year
        if month_name == 'february' and day_num == 29:
            day_num = 28
            print(f"Testing {test_date.strftime('%B %d, %Y')} (Leap year → Feb 28):")
        else:
            print(f"Testing {test_date.strftime('%B %d, %Y')}:")

        # Find the quote
        month_quotes = quotes_db.get(month_name, [])
        quote_found = None

        for quote_entry in month_quotes:
            if quote_entry['day'] == day_num:
                quote_found = quote_entry
                break

        if quote_found:
            print(f"  ✓ Quote found")
            print(f"    Attribution: {quote_found['attribution']}")
            print(f"    Theme: {quote_found['theme']}")
            print(f"    Quote: {quote_found['quote'][:60]}...")
        else:
            print(f"  ✗ Quote NOT found for {month_name} {day_num}")
            all_passed = False

        print()

    if all_passed:
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(test_quote_loader())
