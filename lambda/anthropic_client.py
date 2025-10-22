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


def build_prompt(theme: str, used_quotes: List[str]) -> str:
    """
    Build the prompt for Claude to generate a stoic reflection.

    Args:
        theme: Monthly theme (e.g., "Discipline and Self-Improvement")
        used_quotes: List of recently used quote attributions to avoid

    Returns:
        Formatted prompt string
    """
    # Format exclusion list
    if used_quotes:
        exclusion_list = "\n".join([f"- {quote}" for quote in used_quotes])
    else:
        exclusion_list = "(No quotes to exclude - this is the first reflection)"

    prompt = f"""You are a thoughtful teacher of stoic philosophy. Your task is to create a daily reflection for someone interested in applying stoic wisdom to modern life.

Current Month's Theme: {theme}

Requirements:
1. Select ONE quote from classical stoic texts:
   - Marcus Aurelius (Meditations)
   - Epictetus (Discourses or Enchiridion)
   - Seneca (Letters or Essays)
   - Musonius Rufus (Lectures)

2. The quote should relate to this month's theme: {theme}

3. Do NOT use any of these recently used quotes:
{exclusion_list}

4. Write a reflection (250-450 words) that:
   - Explains the quote's meaning in accessible language
   - Connects it to modern life with a concrete, relatable example
   - Offers practical, actionable guidance the reader can apply today
   - Uses a warm, conversational tone (imagine speaking to a thoughtful friend)
   - Avoids academic jargon or overly formal language
   - Feels personal and encouraging, not preachy or didactic

5. Format your response as JSON:
{{
  "quote": "The exact quote text",
  "attribution": "Author - Work Section (e.g., 'Marcus Aurelius - Meditations 4.3')",
  "reflection": "Your full reflection text here"
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
        Dictionary with 'quote', 'attribution', and 'reflection' keys

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
        result = parse_anthropic_response(response_text)

        return result

    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        raise


def parse_anthropic_response(response_text: str) -> Dict[str, str]:
    """
    Parse Claude's response and extract structured data.

    Handles both raw JSON and JSON wrapped in markdown code blocks.

    Args:
        response_text: Raw response text from Claude

    Returns:
        Dictionary with 'quote', 'attribution', and 'reflection' keys

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
        required_fields = ['quote', 'attribution', 'reflection']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            if not data[field] or not isinstance(data[field], str):
                raise ValueError(f"Invalid value for field: {field}")

        logger.info("Successfully parsed Anthropic response")
        logger.info(f"Quote attribution: {data['attribution']}")

        return {
            'quote': data['quote'].strip(),
            'attribution': data['attribution'].strip(),
            'reflection': data['reflection'].strip()
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


def generate_reflection(
    theme: str,
    used_quotes: List[str],
    api_key: str
) -> Optional[Dict[str, str]]:
    """
    High-level function to generate a complete reflection.

    Args:
        theme: Monthly theme name
        used_quotes: List of recently used quote attributions
        api_key: Anthropic API key

    Returns:
        Dictionary with quote, attribution, and reflection, or None if generation fails
    """
    try:
        prompt = build_prompt(theme, used_quotes)
        result = call_anthropic_api(prompt, api_key)

        # Validate attribution format
        if not validate_attribution_format(result['attribution']):
            logger.warning(
                f"Attribution format may be unusual: {result['attribution']}"
            )
            # Don't fail, just log warning

        return result

    except Exception as e:
        logger.error(f"Failed to generate reflection: {e}")
        return None
