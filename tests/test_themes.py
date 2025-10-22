"""Unit tests for themes module."""

import pytest
import sys
from pathlib import Path

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent / "lambda"
sys.path.insert(0, str(lambda_dir))

from themes import get_monthly_theme, get_theme_name, get_theme_description


class TestThemes:
    """Test cases for monthly themes."""

    def test_get_monthly_theme_january(self):
        """Test January theme."""
        theme = get_monthly_theme(1)
        assert theme["name"] == "Discipline and Self-Improvement"
        assert "habits" in theme["description"].lower()

    def test_get_monthly_theme_october(self):
        """Test October theme."""
        theme = get_monthly_theme(10)
        assert theme["name"] == "Mortality and Impermanence"
        assert "memento mori" in theme["description"].lower()

    def test_get_monthly_theme_december(self):
        """Test December theme."""
        theme = get_monthly_theme(12)
        assert theme["name"] == "Reflection and Legacy"
        assert "contemplation" in theme["description"].lower()

    def test_get_monthly_theme_invalid_month_low(self):
        """Test invalid month (too low)."""
        with pytest.raises(ValueError):
            get_monthly_theme(0)

    def test_get_monthly_theme_invalid_month_high(self):
        """Test invalid month (too high)."""
        with pytest.raises(ValueError):
            get_monthly_theme(13)

    def test_get_theme_name(self):
        """Test getting just the theme name."""
        name = get_theme_name(5)
        assert name == "Virtue and Character"

    def test_get_theme_description(self):
        """Test getting just the theme description."""
        description = get_theme_description(6)
        assert "wisdom" in description.lower()

    def test_all_months_have_themes(self):
        """Test that all 12 months have valid themes."""
        for month in range(1, 13):
            theme = get_monthly_theme(month)
            assert "name" in theme
            assert "description" in theme
            assert len(theme["name"]) > 0
            assert len(theme["description"]) > 0
