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
        context_section += """These are examples of reflections already provided to the user this month. Your new reflection should avoid being overly repetitive. While maintaining consistency with the monthly theme, look for fresh angles, different practical applications, and new ways to help the user understand stoic philosophy. Avoid reusing the same examples, metaphors, or phrasing from the previous reflections above.

"""

    prompt = f"""You are a thoughtful teacher of stoic philosophy. Your task is to write a daily reflection for someone interested in applying stoic wisdom to modern life. You must not use the first person pronouns "I" or "me" in your reflection.
{context_section}
You have been given this stoic quote to reflect upon:

"{quote}"
— {attribution}

Current Month's Theme: {theme}

Write a reflection (150-250 words) that:
- Explains the quote's meaning in accessible language
- Connects it to modern life with a concrete, relatable example
- Offers practical, actionable guidance the reader can apply today
- Uses a warm, conversational tone (imagine speaking to a thoughtful friend)
- Avoids academic jargon or overly formal language
- Feels personal and encouraging, not preachy or didactic

Format your response as JSON:
{{
  "reflection": "Your full reflection text here"
}}

Write the reflection now."""

    return prompt


def call_anthropic_api(prompt: str, api_key: str, timeout: int = 25) -> str:
    """
    Call the Anthropic API to generate a stoic reflection.

    Args:
        prompt: The formatted prompt
        api_key: Anthropic API key
        timeout: API call timeout in seconds (default: 25)

    Returns:
        The reflection text

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


def parse_reflection_response(response_text: str) -> str:
    """
    Parse Claude's response and extract the reflection text.

    Handles both raw JSON and JSON wrapped in markdown code blocks.

    Args:
        response_text: Raw response text from Claude

    Returns:
        The reflection text string

    Raises:
        ValueError: If response is invalid or missing reflection field
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

        # Validate reflection field
        if 'reflection' not in data:
            raise ValueError("Missing required field: reflection")
        if not data['reflection'] or not isinstance(data['reflection'], str):
            raise ValueError("Invalid value for field: reflection")

        logger.info("Successfully parsed Anthropic response")
        reflection_length = len(data['reflection'])
        logger.info(f"Reflection length: {reflection_length} characters")

        return data['reflection'].strip()

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
) -> Optional[str]:
    """
    Generate a reflection based on a provided quote.

    Args:
        quote: The stoic quote to reflect upon
        attribution: The quote's attribution (e.g., "Marcus Aurelius - Meditations 5.1")
        theme: Monthly theme name
        api_key: Anthropic API key
        previous_reflections: List of previous quotes and reflections from this month

    Returns:
        The reflection text, or None if generation fails
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
