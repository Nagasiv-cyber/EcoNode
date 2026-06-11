"""
Agent and API logic for EcoNode.

Version: 2.1.0
"""
__version__ = "2.1.0"

import time
import datetime
import streamlit as st
import google.generativeai as genai

from config import MASTER_PROMPT, ApiResponse, DAILY_CEILING_KG
from utils import extract_json

@st.cache_resource
def get_gemini_model(api_key: str):
    """
    Instantiate and cache the Gemini model to avoid re-initialization.
    
    Args:
        api_key (str): The Google Gemini API Key.
        
    Returns:
        genai.GenerativeModel: The configured model instance.
    """
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
        system_instruction=MASTER_PROMPT,
    )

def call_gemini(user_text: str, ledger: str, api_key: str) -> ApiResponse:
    """
    Call the Gemini API with the given payload.
    
    Args:
        user_text (str): The sanitized user log input.
        ledger (str): The historical ledger state.
        api_key (str): The Gemini API Key.
        
    Returns:
        ApiResponse: The parsed JSON dictionary from the model.
    """
    model = get_gemini_model(api_key)
    payload = f"""
[CONTEXTUAL BOUNDARY CONDITIONS]
- Current System Date: {datetime.datetime.utcnow().strftime('%Y-%m-%d')}
- Standard Maximum Ceiling: {DAILY_CEILING_KG} kg CO2e
- Missing Fields Handling: If a data type (e.g., Diet or Energy) is absent from the input, assign an impact of 0.00 kg CO2e and mark its agent insight as 'No active logging detected for this sector.'

[HISTORICAL LEDGER BASELINE]
{ledger}

[USER INPUT PAYLOAD]
{user_text}

EXECUTION INSTRUCTION:
Parse the payload above, calculate the total metrics utilizing the Emission Factor Matrix, apply the ledger rules, and generate the pure JSON response matching the required schema.
"""
    response = model.generate_content(payload)
    return extract_json(response.text)

def mock_response(user_text: str) -> ApiResponse:
    """
    Provide a deterministic mock response for demo mode.
    
    Args:
        user_text (str): The raw user input.
        
    Returns:
        ApiResponse: A mocked JSON dictionary.
    """
    time.sleep(2.2)  # Simulate API latency
    return {
        "execution_timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "system_status": "WARNING",
        "ingestion_metrics": {
            "workloads_detected": [
                "Transit: Gasoline sedan — 22 km commute",
                "Transit: Electric auto-rickshaw — 4 km lunch trip",
                "Diet: South Indian breakfast (Idli & Sambar)",
                "Diet: Chicken biryani — lunch",
                "Diet: Plant-based dinner (Dal & Rice)",
                "Energy: Workspace AC — 6 h continuous @ 21 °C",
                "Compute: GreenArb backtest — RTX 4070 Laptop, 3.5 h peak grid (14:00–17:30 IST)",
            ],
            "total_co2e_kg": 15.61,
        },
        "emission_breakdown": {
            "Gasoline Sedan (22 km)":   4.62,
            "Electric Rickshaw (4 km)": 0.02,
            "Breakfast – Idli/Sambar":  0.50,
            "Lunch – Chicken Biryani":  2.10,
            "Dinner – Dal & Rice":      0.40,
            "Workspace AC (6 h)":       7.38,
            "GPU Compute (3.5 h)":      0.59,
        },
        "agent_outputs": {
            "compute_optimizations": (
                "GreenOps Directive: GreenArb executed during peak thermal window (14:00–17:30 IST, "
                "grid intensity ×1.18 multiplier applied). Actual compute emission: 0.59 kg CO2e. "
                "Recommendation #1 — TIME-SHIFT: Defer next GreenArb cycle to 00:00–04:00 IST "
                "(off-peak grid, ×0.76 factor). Projected saving: ~0.20 kg CO2e per session."
            ),
            "lifestyle_optimizations": (
                "Hotspot Ranking: (1) Workspace AC 7.38 kg [47.3%] (2) Gasoline Sedan 4.62 kg [29.6%] "
                "(3) Chicken Biryani 2.10 kg [13.5%]. "
                "Recommendation #1 — AC SETPOINT: Raise 21°C → 24°C (BEE India standard)."
            ),
            "ledger_state": (
                "LEDGER REPORT — June 11, 2026 | "
                "Yesterday (June 10): 18.50 kg CO2e → Deficit: −3.50 kg. "
                "Today adjusted ceiling: 11.50 kg (15.0 − 3.50 carryover). "
                "Today actual: 15.61 kg. Overshoot vs adjusted ceiling: +4.11 kg. "
                "Gamified Rank: 🔴 Carbon Debtor L2 — Day 2 consecutive deficit."
            ),
        },
        "deployment_directive": (
            "Raise AC setpoint to 24 °C immediately and plan WFH for June 12 to stay within "
            "the 10.89 kg rebalancing ceiling and prevent a 3-day CRITICAL cascade."
        ),
    }

def run_orchestrator(user_text: str, ledger: str, api_key: str = "") -> ApiResponse:
    """
    Route the request to the API or the mock depending on credentials.
    
    Args:
        user_text (str): Sanitized user text.
        ledger (str): Ledger text.
        api_key (str): API key (optional).
        
    Returns:
        ApiResponse: Evaluated payload.
    """
    if api_key:
        try:
            return call_gemini(user_text, ledger, api_key)
        except Exception as exc:
            st.toast(f"⚠️ Gemini error: {exc} — falling back to demo mode", icon="⚠️")
    return mock_response(user_text)
