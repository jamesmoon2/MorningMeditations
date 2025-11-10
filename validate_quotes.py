#!/usr/bin/env python3
"""
Validate the 365-day quotes database.

Checks that all 365 days are present and properly formatted.
"""

import json
import sys
from pathlib import Path


def validate_quotes_database(file_path: str) -> dict:
    """
    Validate the quotes database contains all 365 days.

    Returns:
        Dictionary with validation results
    """
    with open(file_path, "r") as f:
        quotes_db = json.load(f)

    expected_days = {
        "january": 31,
        "february": 28,
        "march": 31,
        "april": 30,
        "may": 31,
        "june": 30,
        "july": 31,
        "august": 31,
        "september": 30,
        "october": 31,
        "november": 30,
        "december": 31,
    }

    total_quotes = 0
    missing_days = []
    duplicate_days = []
    missing_fields = []

    for month, expected_count in expected_days.items():
        if month not in quotes_db:
            missing_days.extend([(month, day) for day in range(1, expected_count + 1)])
            continue

        month_quotes = quotes_db[month]
        total_quotes += len(month_quotes)

        # Check for all days present
        days_found = set()
        for quote_entry in month_quotes:
            # Validate required fields
            required_fields = ["day", "theme", "quote", "attribution"]
            for field in required_fields:
                if field not in quote_entry:
                    missing_fields.append((month, quote_entry.get("day", "?"), field))

            day = quote_entry.get("day")
            if day in days_found:
                duplicate_days.append((month, day))
            days_found.add(day)

        # Find missing days
        for day in range(1, expected_count + 1):
            if day not in days_found:
                missing_days.append((month, day))

    is_complete = (
        len(missing_days) == 0
        and len(duplicate_days) == 0
        and len(missing_fields) == 0
        and total_quotes == 365
    )

    return {
        "complete": is_complete,
        "total_quotes": total_quotes,
        "expected_quotes": 365,
        "missing_days": missing_days,
        "duplicate_days": duplicate_days,
        "missing_fields": missing_fields,
    }


def main():
    quotes_file = Path(__file__).parent / "config" / "stoic_quotes_365_days.json"

    if not quotes_file.exists():
        print(f"Error: Quotes file not found at {quotes_file}")
        sys.exit(1)

    print("Validating quotes database...")
    print(f"File: {quotes_file}")
    print()

    result = validate_quotes_database(str(quotes_file))

    if result["complete"]:
        print("✓ VALIDATION PASSED")
        print(f"  Total quotes: {result['total_quotes']}/365")
        print(f"  All months complete!")
        sys.exit(0)
    else:
        print("✗ VALIDATION FAILED")
        print(f"  Total quotes: {result['total_quotes']}/365")
        print()

        if result["missing_days"]:
            print(f"  Missing days ({len(result['missing_days'])}):")
            for month, day in result["missing_days"][:10]:  # Show first 10
                print(f"    - {month.title()} {day}")
            if len(result["missing_days"]) > 10:
                print(f"    ... and {len(result['missing_days']) - 10} more")
            print()

        if result["duplicate_days"]:
            print(f"  Duplicate days ({len(result['duplicate_days'])}):")
            for month, day in result["duplicate_days"]:
                print(f"    - {month.title()} {day}")
            print()

        if result["missing_fields"]:
            print(f"  Missing fields ({len(result['missing_fields'])}):")
            for month, day, field in result["missing_fields"][:10]:
                print(f"    - {month.title()} {day}: missing '{field}'")
            if len(result["missing_fields"]) > 10:
                print(f"    ... and {len(result['missing_fields']) - 10} more")

        sys.exit(1)


if __name__ == "__main__":
    main()
