"""EcoNode utility functions for JSON extraction, input validation, and UI helpers."""

__version__ = "2.1.0"

import html
import json
import re
from typing import Any, Dict

from config import ApiResponse, MAX_INPUT_LENGTH

def sanitize_input(user_text: str) -> str:
    """Sanitize user input to prevent XSS and ensure safe logging.

    Args:
        user_text: The raw user input.

    Returns:
        HTML-escaped string.
    """
    return html.escape(user_text.strip())

def validate_input_length(user_text: str) -> str:
    """Validate that the input length does not exceed maximum allowed.

    Args:
        user_text: The user input.

    Returns:
        The validated input string if it passes.

    Raises:
        ValueError: If the input exceeds MAX_INPUT_LENGTH.
    """
    if len(user_text) > MAX_INPUT_LENGTH:
        raise ValueError(f"Input exceeds maximum allowed length of {MAX_INPUT_LENGTH} characters.")
    return user_text

def validate_response_schema(parsed_json: Dict[str, Any]) -> ApiResponse:
    """Validate that the parsed JSON meets the required schema.

    Args:
        parsed_json: The dictionary to validate.

    Returns:
        The validated and strongly typed ApiResponse dictionary.

    Raises:
        KeyError: If a required key is missing.
    """
    required_keys = [
        "execution_timestamp", "system_status", "ingestion_metrics",
        "agent_outputs", "deployment_directive"
    ]
    for key in required_keys:
        if key not in parsed_json:
            raise KeyError(f"Schema validation failed: Missing required key '{key}'")

    # Guarantee emission_breakdown exists for UI
    if "emission_breakdown" not in parsed_json:
        parsed_json["emission_breakdown"] = {}

    # We ignore strict structural type checking of sub-dicts here for brevity,
    # but the presence of keys ensures basic safety.
    return parsed_json  # type: ignore

def extract_json(text: str) -> ApiResponse:
    """Robustly extract a JSON object from an AI response string.

    Args:
        text: The raw text response from the LLM.

    Returns:
        The parsed JSON dictionary adhering to the TypedDict schema.

    Raises:
        ValueError: If no valid JSON is found.
        KeyError: If required schema keys are missing.
    """
    text = text.strip()
    parsed_json = None

    # 1. Direct parse
    try:
        parsed_json = json.loads(text)
    except Exception:
        pass

    # 2. Strip markdown fences
    if not parsed_json:
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence:
            try:
                parsed_json = json.loads(fence.group(1))
            except Exception:
                pass

    # 3. First brace-to-brace block
    if not parsed_json:
        brace = re.search(r"\{[\s\S]*\}", text)
        if brace:
            try:
                parsed_json = json.loads(brace.group(0))
            except Exception:
                pass

    if not parsed_json:
        raise ValueError("No valid JSON object found in model response.")

    return validate_response_schema(parsed_json)
