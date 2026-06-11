"""Pytest suite for EcoNode.

Version: 2.1.0
"""
__version__ = "2.1.0"

from unittest.mock import patch

import pytest

from agents import mock_response, run_orchestrator
from config import MAX_INPUT_LENGTH
from ui import budget_bar_html
from utils import extract_json, sanitize_input, validate_input_length, validate_response_schema

# ── Utils Tests ─────────────────────────────────────────────────────────────

def test_sanitize_input():
    """Verify standard script tags are escaped."""
    raw = "<script>alert('xss')</script>"
    clean = sanitize_input(raw)
    assert "<script>" not in clean
    assert "&lt;script&gt;" in clean

def test_sanitize_input_empty():
    """Verify empty string returns empty."""
    assert sanitize_input("") == ""

def test_sanitize_input_quotes():
    """Verify quotes are escaped."""
    assert sanitize_input('"quote"') == '&quot;quote&quot;'

def test_sanitize_input_strips_html():
    """Verify complex HTML strings are fully sanitized."""
    result = sanitize_input("<script>alert('xss')</script>hello")
    assert "<script>" not in result
    assert "hello" in result

def test_validate_input_length_valid():
    """Verify string below limit is valid."""
    text = "A" * 100
    assert validate_input_length(text) == text

def test_validate_input_length_empty():
    """Verify empty string is valid."""
    assert validate_input_length("") == ""

def test_validate_input_length_invalid():
    """Verify string above limit raises ValueError."""
    text = "A" * (MAX_INPUT_LENGTH + 1)
    with pytest.raises(ValueError):
        validate_input_length(text)

def test_validate_input_length_too_long():
    """Explicit matching test for input length exception."""
    long_input = "a" * 2001
    with pytest.raises(ValueError, match="Input exceeds"):
        validate_input_length(long_input)

def test_validate_input_length_ok():
    """Explicit valid input check."""
    assert validate_input_length("hello") == "hello"

def test_extract_json_valid():
    """Verify basic JSON extraction."""
    raw = '{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}'
    res = extract_json(raw)
    assert res["system_status"] == "O"

def test_extract_json_markdown():
    """Verify extraction handles markdown blocks."""
    raw = '```json\n{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}\n```'
    res = extract_json(raw)
    assert res["system_status"] == "O"

def test_extract_json_braces():
    """Verify extraction drops prefix/suffix fluff."""
    raw = 'Here is the JSON:\n{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}\nDone.'
    res = extract_json(raw)
    assert res["system_status"] == "O"

def test_extract_json_invalid():
    """Verify invalid JSON payload structure raises ValueError."""
    with pytest.raises(ValueError):
        extract_json("No json here")

def test_extract_json_malformed():
    """Verify malformed JSON syntax raises ValueError."""
    with pytest.raises(ValueError):
        extract_json('{"key": "value", }')  # Invalid JSON

def test_extract_json_missing_keys():
    """Verify JSON with missing keys raises KeyError from validate_response_schema."""
    raw = '{"system_status": "O"}'
    with pytest.raises(KeyError):
        extract_json(raw)

def test_extract_json_adds_breakdown():
    """Verify emission_breakdown is auto-injected if missing."""
    raw = '{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}'
    res = extract_json(raw)
    assert "emission_breakdown" in res

def test_validate_response_schema_missing_key():
    """Verify schema validator throws on missing strict keys."""
    bad = {"system_status": "OPTIMAL"}
    with pytest.raises(KeyError):
        validate_response_schema(bad)

def test_extract_json_with_markdown_fence():
    """Test standard markdown fence stripping."""
    text = '```json\n{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}\n```'
    result = extract_json(text)
    assert result["system_status"] == "O"

def test_extract_json_plain():
    """Test plain string json parse fallback."""
    # Note: Using valid full schema string so validate_response_schema doesn't throw
    result = extract_json('{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": "", "a": 1}')
    assert result["a"] == 1

def test_extract_json_invalid_raises():
    """Test extraction failure throws ValueError."""
    with pytest.raises(ValueError):
        extract_json("not json at all !!!")

# ── UI Tests ────────────────────────────────────────────────────────────────

def test_budget_bar_html_normal():
    """Verify green bar HTML."""
    html = budget_bar_html(5.0, 15.0)
    assert "33.3%" in html
    assert "#10b981" in html

def test_budget_bar_html_warning():
    """Verify yellow bar HTML."""
    html = budget_bar_html(13.0, 15.0)
    assert "86.7%" in html
    assert "#f59e0b" in html

def test_budget_bar_html_critical():
    """Color must be red (#ef4444) when usage exceeds ceiling."""
    html = budget_bar_html(16.0, 15.0)
    assert "#ef4444" in html

def test_budget_bar_html_zero_ceiling():
    """Verify edge case of 0 ceiling limits to 100% fill."""
    html = budget_bar_html(5.0, 0.0)
    assert "100.0%" in html  # Maxes out to 100%

@pytest.mark.parametrize("used,ceiling,expected_color", [
    (5.0, 15.0, "#10b981"),   # green: 33%
    (12.0, 15.0, "#f59e0b"),  # yellow: 80%
    (16.0, 15.0, "#ef4444"),  # red: 107%
])
def test_budget_bar_colors_parametrized(used, ceiling, expected_color):
    """Test all color boundary transitions dynamically."""
    html = budget_bar_html(used, ceiling)
    assert expected_color in html

# ── Agents Tests ────────────────────────────────────────────────────────────

def test_mock_response():
    """Verify mock payload contains correct logic fallback."""
    res = mock_response("test")
    assert res["system_status"] == "WARNING"
    assert res["ingestion_metrics"]["total_co2e_kg"] == 15.61

@patch("agents.call_gemini")
def test_run_orchestrator_with_key(mock_call):
    """Verify API call happens if key is present."""
    mock_call.return_value = {"system_status": "OPTIMAL"}
    res = run_orchestrator("test", "ledger", "fake_key")
    assert res["system_status"] == "OPTIMAL"
    mock_call.assert_called_once_with("test", "ledger", "fake_key")

def test_run_orchestrator_without_key():
    """Verify mock triggers when no key is present."""
    res = run_orchestrator("test", "ledger", "")
    assert res["system_status"] == "WARNING"  # Comes from mock_response

@patch("agents.st.toast")
@patch("agents.call_gemini")
def test_run_orchestrator_fallback_on_error(mock_call, mock_toast):
    """Verify orchestrator falls back to mock upon API exception."""
    mock_call.side_effect = Exception("API Down")
    res = run_orchestrator("test", "ledger", "fake_key")
    assert res["system_status"] == "WARNING"  # Comes from mock_response
    mock_toast.assert_called_once()

def test_run_orchestrator_rate_limit():
    """Should raise after MAX_API_CALLS_PER_SESSION exceeded."""
    from config import MAX_API_CALLS_PER_SESSION
    with pytest.raises(RuntimeError, match="Rate limit"):
        run_orchestrator("test", "ledger", "fakekey",
                        call_count=MAX_API_CALLS_PER_SESSION + 1)
