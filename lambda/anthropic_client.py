"""
Anthropic API client for generating daily stoic reflections.

Handles prompt construction, API calls to Claude, and response parsing.
"""

import json
import logging
import re
from typing import Dict, List, Optional
from anthropic import Anthropic

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def build_reflection_prompt(
    quote: str,
    attribution: str,
    theme: str,
    previous_reflections: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Build the prompt for Claude to generate a reflection based on a provided quote.

    Args:
        quote: The stoic quote to reflect upon
        attribution: The quote's attribution (e.g., "Marcus Aurelius - Meditations 5.1")
        theme: Monthly theme (e.g., "Discipline and Self-Improvement")
        previous_reflections: List of previous quotes and reflections from this month
                             Each dict should have: date, quote, attribution, reflection

    Returns:
        Formatted prompt string
    """
    # Build context section from previous reflections if available
    context_section = ""
    if previous_reflections and len(previous_reflections) > 0:
        context_section = "\n\nPrevious quotes and reflections from this month:\n\n"
        for entry in previous_reflections:
            context_section += f"""Date: {entry.get('date', 'Unknown')}
Quote: "{entry.get('quote', '')}"
Attribution: {entry.get('attribution', '')}
Reflection: {entry.get('reflection', '')}

---

"""
        context_section += """These are examples of reflections already provided to the user this month. Your new reflection should build on this foundation by:
- Exploring different aspects of stoic philosophy (virtue, dichotomy of control, negative visualization, memento mori, amor fati, etc.)
- Varying the philosophical angle or school of thought when possible
- Introducing fresh perspectives the user may not have considered
- Avoiding repetition of examples, metaphors, or phrasing from previous reflections

Use this memory to ensure the user experiences a rich, diverse exploration of how ancient wisdom applies to their modern life.

"""

    prompt = f"""You are a thoughtful teacher of stoic philosophy. Your task is to write a daily reflection for someone navigating the complexities of modern life in 2025. You must not use the first person pronouns "I" or "me" in your reflection.
{context_section}
You have been given this stoic quote to reflect upon:

"{quote}"
— {attribution}

Current Month's Theme: {theme}

Write a reflection (150-250 words) that bridges ancient wisdom with contemporary challenges:

THEMATIC FOUNDATION:
- This month's theme ({theme}) is your central organizing principle
- Every reflection must clearly connect to and deepen the reader's understanding of this theme
- Show how the quote illuminates a specific aspect or dimension of the monthly theme
- Help readers build a cohesive understanding of the theme throughout the month

CONTENT FOCUS:
- Explain the quote's meaning in accessible language
- Connect it to real 2025 challenges: workplace stress, difficult relationships, major decisions, financial pressures, information overload, social media anxiety, work-life balance, uncertainty about the future, or everyday struggles we all face
- Draw unexpected connections that help readers see familiar problems through a fresh philosophical lens
- Offer practical, actionable guidance the reader can apply today

PHILOSOPHICAL APPROACH (within the theme):
- When previous reflections exist, explore DIFFERENT ASPECTS of the monthly theme rather than repeating the same angle
- Vary how stoic philosophy applies to this theme (e.g., for a "Resilience" theme: one day focus on accepting what we can't control, another day on building inner strength, another on learning from adversity)
- Help readers build a diverse mental toolkit by showing multiple pathways to understanding and embodying this month's theme
- Make philosophy feel relevant and alive, not abstract or ancient

TONE & STYLE:
- Warm, conversational tone (imagine speaking to a thoughtful friend over coffee)
- Avoid academic jargon or overly formal language
- Feel personal and encouraging, not preachy or didactic
- Meet readers where they are with empathy and understanding

STRUCTURE:
Your reflection should be organized into three distinct sections:

1. UNDERSTANDING (40-60 words): Explain the quote's core meaning in accessible, everyday language. What is the philosopher really saying here?

2. CONNECTION (60-80 words): Connect this wisdom to specific 2025 challenges with concrete examples. Think: workplace stress, difficult relationships, major decisions, financial pressures, information overload, social media anxiety, work-life balance, uncertainty, or daily struggles. Make the ancient wisdom feel immediately relevant to modern life.

3. DAILY PRACTICE (50-60 words): Offer a specific micro-practice the reader can apply TODAY. Be concrete and actionable - not generic advice. Examples: "Before your next meeting, take 30 seconds to..." or "Tonight, write down three things..." Give them a clear, simple action they can take within the next 24 hours.

Format your response as JSON:
{{
  "understanding": "Your explanation of the quote's meaning (40-60 words)",
  "connection": "How this applies to 2025 challenges with concrete examples (60-80 words)",
  "practice": "A specific micro-practice for today (50-60 words)"
}}

Write the reflection now."""

    return prompt


def call_anthropic_api(prompt: str, api_key: str, timeout: int = 25) -> Dict[str, str]:
    """
    Call the Anthropic API to generate a stoic reflection.

    Args:
        prompt: The formatted prompt
        api_key: Anthropic API key
        timeout: API call timeout in seconds (default: 25)

    Returns:
        Dictionary with keys: understanding, connection, practice

    Raises:
        Exception: If API call fails or response is invalid
    """
    try:
        client = Anthropic(api_key=api_key)

        logger.info("Calling Anthropic API to generate reflection")

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            temperature=1.0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            timeout=timeout
        )

        # Extract text from response
        response_text = response.content[0].text

        logger.info(f"Received response from Anthropic API ({len(response_text)} chars)")

        # Parse the response
        reflection = parse_reflection_response(response_text)

        return reflection

    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        raise


def parse_reflection_response(response_text: str) -> Dict[str, str]:
    """
    Parse Claude's response and extract the structured reflection.

    Handles both raw JSON and JSON wrapped in markdown code blocks.

    Args:
        response_text: Raw response text from Claude

    Returns:
        Dictionary with keys: understanding, connection, practice

    Raises:
        ValueError: If response is invalid or missing required fields
    """
    try:
        # Try to extract JSON from markdown code blocks first
        json_match = re.search(
            r'```(?:json)?\s*(\{.*?\})\s*```',
            response_text,
            re.DOTALL
        )

        if json_match:
            json_str = json_match.group(1)
            logger.info("Found JSON in markdown code block")
        else:
            # Try to parse the entire response as JSON
            json_str = response_text.strip()
            logger.info("Attempting to parse response as raw JSON")

        # Parse JSON
        data = json.loads(json_str)

        # Validate required fields
        required_fields = ['understanding', 'connection', 'practice']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            if not data[field] or not isinstance(data[field], str):
                raise ValueError(f"Invalid value for field: {field}")

        logger.info("Successfully parsed Anthropic response")
        total_length = sum(len(data[field]) for field in required_fields)
        logger.info(f"Total reflection length: {total_length} characters")
        logger.info(f"Understanding: {len(data['understanding'])} chars, "
                   f"Connection: {len(data['connection'])} chars, "
                   f"Practice: {len(data['practice'])} chars")

        return {
            'understanding': data['understanding'].strip(),
            'connection': data['connection'].strip(),
            'practice': data['practice'].strip()
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from response: {e}")
        logger.error(f"Response text: {response_text[:500]}...")
        raise ValueError(f"Invalid JSON in API response: {e}")

    except Exception as e:
        logger.error(f"Error parsing Anthropic response: {e}")
        raise


def validate_attribution_format(attribution: str) -> bool:
    """
    Validate that attribution follows expected format.

    Expected format: "Author - Work Section" or "Author - Work"

    Args:
        attribution: Attribution string to validate

    Returns:
        True if valid format, False otherwise
    """
    # Should contain author name and work separated by dash
    if ' - ' not in attribution:
        return False

    parts = attribution.split(' - ')
    if len(parts) < 2:
        return False

    # Check for known authors
    known_authors = [
        'Marcus Aurelius',
        'Epictetus',
        'Seneca',
        'Musonius Rufus'
    ]

    author = parts[0].strip()
    return any(known in author for known in known_authors)


def generate_reflection_only(
    quote: str,
    attribution: str,
    theme: str,
    api_key: str,
    previous_reflections: Optional[List[Dict[str, str]]] = None
) -> Optional[Dict[str, str]]:
    """
    Generate a reflection based on a provided quote.

    Args:
        quote: The stoic quote to reflect upon
        attribution: The quote's attribution (e.g., "Marcus Aurelius - Meditations 5.1")
        theme: Monthly theme name
        api_key: Anthropic API key
        previous_reflections: List of previous quotes and reflections from this month

    Returns:
        Dictionary with keys: understanding, connection, practice, or None if generation fails
    """
    try:
        # Validate attribution format
        if not validate_attribution_format(attribution):
            logger.warning(
                f"Attribution format may be unusual: {attribution}"
            )
            # Don't fail, just log warning

        prompt = build_reflection_prompt(quote, attribution, theme, previous_reflections)
        reflection = call_anthropic_api(prompt, api_key)

        return reflection

    except Exception as e:
        logger.error(f"Failed to generate reflection: {e}")
        return None
