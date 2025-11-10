"""Unit tests for email_formatter module."""

import sys
from pathlib import Path

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent / "lambda"
sys.path.insert(0, str(lambda_dir))

from email_formatter import (
    format_html_email,
    format_plain_text_email,
    create_email_subject,
    validate_email_content,
    format_reflection_paragraphs,
)


class TestEmailFormatter:
    """Test cases for email formatting."""

    def test_format_html_email(self):
        """Test HTML email generation."""
        quote = "You have power over your mind - not outside events."
        attribution = "Marcus Aurelius - Meditations 6.8"
        reflection = "This is a test reflection about the power of the mind."
        theme = "Discipline and Self-Improvement"

        html = format_html_email(quote, attribution, reflection, theme)

        # Check that all elements are present
        assert quote in html
        assert attribution in html
        assert reflection in html
        assert theme in html

        # Check for HTML structure
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<style>" in html

    def test_format_plain_text_email(self):
        """Test plain text email generation."""
        quote = "The impediment to action advances action."
        attribution = "Marcus Aurelius - Meditations 5.20"
        reflection = "Test reflection text."

        plain = format_plain_text_email(quote, attribution, reflection)

        # Check that all elements are present
        assert quote in plain
        assert attribution in plain
        assert reflection in plain
        assert "MORNING STOIC REFLECTION" in plain

    def test_create_email_subject(self):
        """Test email subject creation."""
        theme = "Virtue and Character"
        subject = create_email_subject(theme)

        assert "Morning Stoic Reflection" in subject
        assert theme in subject

    def test_validate_email_content_valid(self):
        """Test validation with valid content."""
        quote = "Test quote"
        attribution = "Marcus Aurelius - Meditations 2.1"
        reflection = " ".join(["word"] * 250)  # 250 words

        validation = validate_email_content(quote, attribution, reflection)

        assert validation["has_quote"] is True
        assert validation["has_attribution"] is True
        assert validation["has_reflection"] is True
        assert validation["reflection_min_length"] is True
        assert validation["is_valid"] is True

    def test_validate_email_content_too_short(self):
        """Test validation with too short reflection."""
        quote = "Test quote"
        attribution = "Marcus Aurelius - Meditations 2.1"
        reflection = "Too short"

        validation = validate_email_content(quote, attribution, reflection)

        assert validation["reflection_min_length"] is False
        assert validation["is_valid"] is False

    def test_validate_email_content_missing_quote(self):
        """Test validation with missing quote."""
        quote = ""
        attribution = "Marcus Aurelius - Meditations 2.1"
        reflection = " ".join(["word"] * 250)

        validation = validate_email_content(quote, attribution, reflection)

        assert validation["has_quote"] is False
        assert validation["is_valid"] is False

    def test_format_reflection_paragraphs_single(self):
        """Test formatting single paragraph."""
        reflection = "This is a single paragraph reflection."
        formatted = format_reflection_paragraphs(reflection)

        assert "<p>" in formatted
        assert "</p>" in formatted
        assert reflection in formatted

    def test_format_reflection_paragraphs_multiple(self):
        """Test formatting multiple paragraphs."""
        reflection = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        formatted = format_reflection_paragraphs(reflection)

        # Should have 3 <p> tags
        assert formatted.count("<p>") == 3
        assert formatted.count("</p>") == 3
        assert "First paragraph" in formatted
        assert "Second paragraph" in formatted
        assert "Third paragraph" in formatted

    def test_html_escape_special_characters(self):
        """Test that special HTML characters are escaped."""
        quote = "<script>alert('test')</script>"
        attribution = "Test & Author"
        reflection = "Reflection with <tags> & special chars"
        theme = "Test Theme"

        html = format_html_email(quote, attribution, reflection, theme)

        # Should not contain unescaped HTML
        assert "<script>" not in html
        assert "&lt;script&gt;" in html or "alert" not in html
        assert "&amp;" in html or "Test &amp; Author" in html
