"""
Utility functions for EcoNode.

Version: 2.1.0
"""
__version__ = "2.1.0"

import json
import re
import html
from typing import Dict, Any

from config import MAX_INPUT_LENGTH, ApiResponse

def sanitize_input(user_text: str) -> str:
    """
    Sanitize user input to prevent XSS and ensure safe logging.
    
    Args:
        user_text (str): The raw user input.
        
    Returns:
        str: HTML-escaped string.
    """
    return html.escape(user_text.strip())

def validate_input_length(user_text: str) -> bool:
    """
    Validate that the input length does not exceed maximum allowed.
    
    Args:
        user_text (str): The user input.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    return len(user_text) <= MAX_INPUT_LENGTH

def extract_json(text: str) -> ApiResponse:
    """
    Robustly extract a JSON object from an AI response string.
    
    Args:
        text (str): The raw text response from the LLM.
        
    Returns:
        ApiResponse: The parsed JSON dictionary adhering to the TypedDict schema.
        
    Raises:
        ValueError: If no valid JSON is found or if required schema keys are missing.
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
        
    # Validate basic schema presence
    required_keys = [
        "execution_timestamp", "system_status", "ingestion_metrics", 
        "agent_outputs", "deployment_directive"
    ]
    for key in required_keys:
        if key not in parsed_json:
            raise ValueError(f"Schema validation failed: Missing required key '{key}'")
            
    # Guarantee emission_breakdown exists for UI
    if "emission_breakdown" not in parsed_json:
        parsed_json["emission_breakdown"] = {}
        
    return parsed_json
