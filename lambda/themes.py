"""
Monthly themes for stoic reflections.

Each month has a distinct theme that guides quote selection and reflection content.
"""

from typing import Dict, TypedDict


class ThemeInfo(TypedDict):
    """Type definition for theme information."""
    name: str
    description: str


# Monthly themes following the PRD specification
MONTHLY_THEMES: Dict[int, ThemeInfo] = {
    1: {
        "name": "Discipline and Self-Improvement",
        "description": "Focus on building habits, self-control, and starting fresh"
    },
    2: {
        "name": "Relationships and Community",
        "description": "Our connections to others, love, friendship, and social virtue"
    },
    3: {
        "name": "Resilience and Adversity",
        "description": "Facing challenges, growing through difficulty, and mental toughness"
    },
    4: {
        "name": "Nature and Acceptance",
        "description": "Living in accordance with nature, accepting what is"
    },
    5: {
        "name": "Virtue and Character",
        "description": "The four cardinal virtues (wisdom, justice, courage, temperance)"
    },
    6: {
        "name": "Wisdom and Philosophy",
        "description": "The love of wisdom, continuous learning, and philosophical practice"
    },
    7: {
        "name": "Freedom and Autonomy",
        "description": "Inner freedom, independence of mind, and self-sufficiency"
    },
    8: {
        "name": "Patience and Endurance",
        "description": "Long-term thinking, persistence, and bearing hardship"
    },
    9: {
        "name": "Purpose and Calling",
        "description": "Finding meaning, living deliberately, and fulfilling your role"
    },
    10: {
        "name": "Mortality and Impermanence",
        "description": "Memento mori, making the most of time, and perspective on death"
    },
    11: {
        "name": "Gratitude and Contentment",
        "description": "Appreciating what we have, finding sufficiency, and thanksgiving"
    },
    12: {
        "name": "Reflection and Legacy",
        "description": "Year-end contemplation, examining life, and what we leave behind"
    }
}


def get_monthly_theme(month: int) -> ThemeInfo:
    """
    Get the theme information for a given month.

    Args:
        month: Month number (1-12)

    Returns:
        ThemeInfo dictionary with name and description

    Raises:
        ValueError: If month is not in range 1-12
    """
    if month < 1 or month > 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")

    return MONTHLY_THEMES[month]


def get_theme_name(month: int) -> str:
    """
    Get just the theme name for a given month.

    Args:
        month: Month number (1-12)

    Returns:
        Theme name as string
    """
    return get_monthly_theme(month)["name"]


def get_theme_description(month: int) -> str:
    """
    Get just the theme description for a given month.

    Args:
        month: Month number (1-12)

    Returns:
        Theme description as string
    """
    return get_monthly_theme(month)["description"]
