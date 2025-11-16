"""
Email formatting utilities for creating beautiful HTML and plain text emails.

Provides templates and formatting functions for morning stoic reflection emails.
"""

import html
from typing import Dict


def format_html_email(
    quote: str,
    attribution: str,
    reflection: Dict[str, str],
    theme: str,
    day_of_month: int = 1,
    days_in_month: int = 30
) -> str:
    """
    Format the daily reflection as an HTML email.

    Args:
        quote: The stoic quote text
        attribution: Quote attribution (e.g., "Marcus Aurelius - Meditations 4.3")
        reflection: Dictionary with keys: understanding, connection, practice
        theme: Monthly theme name
        day_of_month: Current day of the month (1-31)
        days_in_month: Total days in current month (28-31)

    Returns:
        Complete HTML email as a string
    """
    # Escape HTML special characters
    quote_safe = html.escape(quote)
    attribution_safe = html.escape(attribution)
    theme_safe = html.escape(theme)

    # Format structured reflection sections
    understanding_html = format_reflection_section(reflection.get('understanding', ''))
    connection_html = format_reflection_section(reflection.get('connection', ''))
    practice_html = format_reflection_section(reflection.get('practice', ''))

    # Create progress indicator
    progress_text = f"Day {day_of_month} of {days_in_month}"
    progress_percent = (day_of_month / days_in_month) * 100

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morning Stoic Reflection</title>
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.7;
            color: #2c3e50;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f6fa;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.06);
        }}
        .header {{
            text-align: center;
            margin-bottom: 35px;
            border-bottom: 3px solid #34495e;
            padding-bottom: 25px;
        }}
        .header h1 {{
            margin: 0 0 8px 0;
            color: #1a252f;
            font-size: 32px;
            font-weight: 600;
            letter-spacing: -0.5px;
        }}
        .theme {{
            color: #7f8c8d;
            font-style: italic;
            font-size: 15px;
            margin-top: 8px;
            font-weight: 500;
        }}
        .progress {{
            margin-top: 12px;
            font-size: 13px;
            color: #95a5a6;
        }}
        .progress-bar {{
            height: 4px;
            background-color: #ecf0f1;
            border-radius: 2px;
            margin-top: 6px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2980b9);
            width: {progress_percent}%;
            border-radius: 2px;
        }}
        .section-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #95a5a6;
            margin: 30px 0 12px 0;
        }}
        .quote-section {{
            margin-bottom: 35px;
        }}
        .quote {{
            font-size: 20px;
            font-style: italic;
            color: #2c3e50;
            margin: 0;
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background: linear-gradient(to right, #f8f9fa, #e9ecef);
            border-left: 5px solid #3498db;
            border-radius: 4px;
            line-height: 1.8;
        }}
        .attribution {{
            text-align: right;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 12px;
            font-weight: 500;
        }}
        .reflection-section {{
            background-color: #fafbfc;
            padding: 25px;
            border-radius: 6px;
            margin-bottom: 20px;
            border-left: 4px solid #e0e0e0;
        }}
        .reflection-section.understanding {{
            border-left-color: #3498db;
        }}
        .reflection-section.connection {{
            border-left-color: #9b59b6;
        }}
        .reflection-section.practice {{
            border-left-color: #27ae60;
            background-color: #f0fdf4;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: #2c3e50;
            margin: 0 0 12px 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        .section-title.understanding {{
            color: #2980b9;
        }}
        .section-title.connection {{
            color: #8e44ad;
        }}
        .section-title.practice {{
            color: #229954;
        }}
        .section-content {{
            font-size: 16px;
            line-height: 1.8;
            color: #34495e;
            margin: 0;
        }}
        .footer {{
            margin-top: 45px;
            padding-top: 25px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            font-size: 12px;
            color: #95a5a6;
        }}
        @media only screen and (max-width: 600px) {{
            .container {{
                padding: 25px 20px;
            }}
            .header h1 {{
                font-size: 26px;
            }}
            .quote {{
                font-size: 18px;
                padding: 20px;
            }}
            .section-content {{
                font-size: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Morning Stoic Reflection</h1>
            <div class="theme">{theme_safe}</div>
            <div class="progress">
                {progress_text}
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
        </div>

        <div class="quote-section">
            <div class="section-label">Today's Quote</div>
            <div class="quote">
                {quote_safe}
            </div>
            <div class="attribution">— {attribution_safe}</div>
        </div>

        <div class="section-label">Reflection</div>

        <div class="reflection-section understanding">
            <div class="section-title understanding">💡 Understanding</div>
            <div class="section-content">{understanding_html}</div>
        </div>

        <div class="reflection-section connection">
            <div class="section-title connection">🔗 Connection to 2025</div>
            <div class="section-content">{connection_html}</div>
        </div>

        <div class="reflection-section practice">
            <div class="section-title practice">✓ Today's Practice</div>
            <div class="section-content">{practice_html}</div>
        </div>

        <div class="footer">
            Morning Stoic Reflection • Powered by Claude and James C. Mooney
        </div>
    </div>
</body>
</html>"""

    return html_template


def format_plain_text_email(quote: str, attribution: str, reflection: Dict[str, str]) -> str:
    """
    Format the daily reflection as plain text email (fallback).

    Args:
        quote: The stoic quote text
        attribution: Quote attribution
        reflection: Dictionary with keys: understanding, connection, practice

    Returns:
        Plain text email as a string
    """
    divider = "=" * 70

    understanding = reflection.get('understanding', '')
    connection = reflection.get('connection', '')
    practice = reflection.get('practice', '')

    plain_text = f"""
{divider}
MORNING STOIC REFLECTION
{divider}

"{quote}"

— {attribution}

{divider}

UNDERSTANDING

{understanding}

CONNECTION TO 2025

{connection}

TODAY'S PRACTICE

{practice}

{divider}
Morning Stoic Reflection • Powered by Claude and James C. Mooney
"""

    return plain_text.strip()


def format_reflection_section(text: str) -> str:
    """
    Format a reflection section by escaping HTML.

    Args:
        text: Raw text content

    Returns:
        HTML-escaped text
    """
    # Remove extra whitespace
    cleaned = ' '.join(text.split())
    return html.escape(cleaned)


def format_reflection_paragraphs(reflection: str) -> str:
    """
    Format reflection text into HTML paragraphs.

    DEPRECATED: This function is kept for backward compatibility.
    Use format_reflection_section instead.

    Args:
        reflection: Raw reflection text

    Returns:
        HTML formatted reflection with <p> tags
    """
    # Split on double newlines to detect paragraphs
    paragraphs = reflection.split('\n\n')

    # Escape HTML and wrap in <p> tags
    formatted_paragraphs = []
    for para in paragraphs:
        # Remove extra whitespace and newlines within paragraph
        cleaned = ' '.join(para.split())
        if cleaned:  # Only add non-empty paragraphs
            escaped = html.escape(cleaned)
            formatted_paragraphs.append(f"<p>{escaped}</p>")

    return '\n            '.join(formatted_paragraphs)


def create_email_subject(theme: str) -> str:
    """
    Create the email subject line.

    Args:
        theme: Monthly theme name

    Returns:
        Email subject line
    """
    return f"Morning Stoic Reflection: {theme}"


def validate_email_content(quote: str, attribution: str, reflection: Dict[str, str]) -> Dict[str, bool]:
    """
    Validate email content meets basic requirements.

    Args:
        quote: The stoic quote text
        attribution: Quote attribution
        reflection: Dictionary with keys: understanding, connection, practice

    Returns:
        Dictionary with validation results
    """
    # Calculate total word count across all sections
    understanding = reflection.get('understanding', '')
    connection = reflection.get('connection', '')
    practice = reflection.get('practice', '')

    total_words = (len(understanding.split()) +
                   len(connection.split()) +
                   len(practice.split()))

    validation = {
        "has_quote": bool(quote and len(quote.strip()) > 0),
        "has_attribution": bool(attribution and len(attribution.strip()) > 0),
        "has_understanding": bool(understanding and len(understanding.strip()) > 0),
        "has_connection": bool(connection and len(connection.strip()) > 0),
        "has_practice": bool(practice and len(practice.strip()) > 0),
        "reflection_min_length": total_words >= 150,  # 150 words minimum total
        "reflection_max_length": total_words <= 250,  # 250 words maximum total
    }

    validation["is_valid"] = all([
        validation["has_quote"],
        validation["has_attribution"],
        validation["has_understanding"],
        validation["has_connection"],
        validation["has_practice"],
        validation["reflection_min_length"]
    ])

    return validation
