"""
Pytest suite for EcoNode.

Version: 2.1.0
"""
__version__ = "2.1.0"

import pytest
import json
from unittest.mock import patch, MagicMock

from config import MAX_INPUT_LENGTH, DAILY_CEILING_KG
from utils import sanitize_input, validate_input_length, extract_json
from ui import budget_bar_html
from agents import mock_response, run_orchestrator

# ── Utils Tests ─────────────────────────────────────────────────────────────

def test_sanitize_input():
    raw = "<script>alert('xss')</script>"
    clean = sanitize_input(raw)
    assert "<script>" not in clean
    assert "&lt;script&gt;" in clean

def test_sanitize_input_empty():
    assert sanitize_input("") == ""

def test_sanitize_input_quotes():
    assert sanitize_input('"quote"') == '&quot;quote&quot;'

def test_validate_input_length_valid():
    text = "A" * 100
    assert validate_input_length(text) is True

def test_validate_input_length_empty():
    assert validate_input_length("") is True

def test_validate_input_length_invalid():
    text = "A" * (MAX_INPUT_LENGTH + 1)
    assert validate_input_length(text) is False

def test_extract_json_valid():
    raw = '{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}'
    res = extract_json(raw)
    assert res["system_status"] == "O"

def test_extract_json_markdown():
    raw = '```json\n{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}\n```'
    res = extract_json(raw)
    assert res["system_status"] == "O"

def test_extract_json_braces():
    raw = 'Here is the JSON:\n{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}\nDone.'
    res = extract_json(raw)
    assert res["system_status"] == "O"

def test_extract_json_invalid():
    with pytest.raises(ValueError):
        extract_json("No json here")

def test_extract_json_malformed():
    with pytest.raises(ValueError):
        extract_json('{"key": "value", }')  # Invalid JSON

def test_extract_json_missing_keys():
    raw = '{"system_status": "O"}'
    with pytest.raises(ValueError):
        extract_json(raw)

def test_extract_json_adds_breakdown():
    raw = '{"execution_timestamp": "T", "system_status": "O", "ingestion_metrics": {}, "agent_outputs": {}, "deployment_directive": ""}'
    res = extract_json(raw)
    assert "emission_breakdown" in res

# ── UI Tests ────────────────────────────────────────────────────────────────

def test_budget_bar_html_normal():
    html = budget_bar_html(5.0, 15.0)
    assert "33.3%" in html
    assert "#10b981" in html

def test_budget_bar_html_warning():
    html = budget_bar_html(13.0, 15.0)
    assert "86.7%" in html
    assert "#f59e0b" in html

def test_budget_bar_html_critical():
    html = budget_bar_html(16.0, 15.0)
    assert "100.0%" in html
    assert "#ef4444" in html

def test_budget_bar_html_zero_ceiling():
    html = budget_bar_html(5.0, 0.0)
    assert "100.0%" in html  # Maxes out to 100%

# ── Agents Tests ────────────────────────────────────────────────────────────

def test_mock_response():
    res = mock_response("test")
    assert res["system_status"] == "WARNING"
    assert res["ingestion_metrics"]["total_co2e_kg"] == 15.61

@patch("agents.call_gemini")
def test_run_orchestrator_with_key(mock_call):
    mock_call.return_value = {"system_status": "OPTIMAL"}
    res = run_orchestrator("test", "ledger", "fake_key")
    assert res["system_status"] == "OPTIMAL"
    mock_call.assert_called_once_with("test", "ledger", "fake_key")

def test_run_orchestrator_without_key():
    res = run_orchestrator("test", "ledger", "")
    assert res["system_status"] == "WARNING"  # Comes from mock_response

@patch("agents.st.toast")
@patch("agents.call_gemini")
def test_run_orchestrator_fallback_on_error(mock_call, mock_toast):
    mock_call.side_effect = Exception("API Down")
    res = run_orchestrator("test", "ledger", "fake_key")
    assert res["system_status"] == "WARNING"  # Comes from mock_response
    mock_toast.assert_called_once()
