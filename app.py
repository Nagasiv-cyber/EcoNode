"""EcoNode — Multi-Agent Carbon Intelligence Engine.

A Streamlit-based carbon auditing platform that orchestrates LLM agents to
process multi-modal user activity logs and execute deterministic Carbon
Auditing, GreenOps compute calculation, and Ledger state balancing.

Run with: ``streamlit run app.py``

Version: 2.2.0
"""

__version__ = "2.2.0"

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

import datetime
import html
import json
import re
import time
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE: bool = True
except ImportError:  # pragma: no cover
    PLOTLY_AVAILABLE = False

from google import genai
from google.genai import types


# ═══════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL CONSTANTS  (no magic numbers anywhere below)
# ═══════════════════════════════════════════════════════════════════════════

DAILY_CEILING_KG: float = 15.0
WEEKLY_CEILING_KG: float = 105.0
PEAK_MULTIPLIER: float = 1.18
OFFPEAK_MULTIPLIER: float = 0.76
GASOLINE_FACTOR_KG_PER_KM: float = 0.210
PETROL_SEDAN_KG_PER_KM: float = 0.170
ELECTRIC_AUTO_KG_PER_KM: float = 0.045
INDIA_GRID_INTENSITY: float = 0.820
RTX4070_LOAD_KW: float = 0.115
GPU_KG_PER_HOUR: float = 0.095
AC_DRAW_KW: float = 1.50
CHICKEN_CO2E_KG: float = 1.38
VEG_MEAL_CO2E_KG: float = 0.60
MAX_INPUT_CHARS: int = 2000
MAX_API_CALLS_PER_SESSION: int = 10
DEFICIT_RECOVERY_THRESHOLD_KG: float = 5.0
WEEKLY_MULTIPLIER: int = 7
CHART_COL_RATIO: float = 1.3
LIST_COL_RATIO: float = 1.0
MOCK_LATENCY_SECONDS: float = 2.2
BUDGET_GREEN_THRESHOLD: float = 70.0
BUDGET_YELLOW_THRESHOLD: float = 100.0
BUDGET_MIN_DENOMINATOR: float = 0.01
GPU_COMPUTE_HOURS: float = 2.0
TRANSIT_EMISSION_THRESHOLD: float = 5.0


# ── UI Theme Configuration ──────────────────────────────────────────────────

STATUS_CFG: Dict[str, Dict[str, str]] = {
    "OPTIMAL": {"icon": "🟢", "cls": "eco-optimal", "color": "#10b981"},
    "WARNING": {"icon": "🟡", "cls": "eco-warning", "color": "#f59e0b"},
    "CRITICAL": {"icon": "🔴", "cls": "eco-critical", "color": "#ef4444"},
}

RANK_CFG: Dict[str, Dict[str, str]] = {
    "OPTIMAL": {"label": "🌿 Carbon Neutral", "bg": "#052e16", "fg": "#34d399", "border": "#10b981"},
    "WARNING": {"label": "⚠️ Carbon Debtor L1", "bg": "#451a03", "fg": "#fbbf24", "border": "#f59e0b"},
    "CRITICAL": {"label": "🔴 Carbon Debtor L2", "bg": "#450a0a", "fg": "#f87171", "border": "#ef4444"},
}

CHART_COLORS: List[str] = [
    "#10b981", "#34d399", "#f59e0b", "#ef4444",
    "#8b5cf6", "#06b6d4", "#ec4899", "#f97316",
    "#a3e635", "#fb923c",
]


# ═══════════════════════════════════════════════════════════════════════════
# MASTER SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════

MASTER_PROMPT: str = """
ROLE AND SYSTEM BOUNDARIES:
You are the hyper-optimized Core Inference Engine for EcoNode. Your purpose is to process multi-modal user activity logs and execute deterministic Carbon Auditing, GreenOps compute calculation, and Ledger state balancing. You must operate with 100% logical consistency.

PHASE 1: DETERMINISTIC EMISSION FACTOR MATRIX (R&D GROUNDING)
When evaluating inputs, you must map activities strictly against these scientific baselines:
- Petrol Sedan: 0.170 kg CO2e per km
- Electric Auto-Rickshaw: 0.045 kg CO2e per km (based on Indian grid average)
- High-Efficiency ML Training (NVIDIA RTX 4070 Laptop GPU full load): ~0.095 kg CO2e per hour of active compute.
- Grid Peak Hours (11:00 AM - 6:00 PM): High carbon intensity (coal-dominant baseline).
- Grid Off-Peak Hours (11:00 PM - 5:00 AM): Low carbon intensity (wind/solar integration baseline).
- South Indian Vegetarian Meal (Idli/Sambar/Rice): 0.600 kg CO2e per meal.
- Poultry-based Meal (Chicken Biryani): 2.500 kg CO2e per meal.

PHASE 2: CONTEXTUAL ROUTING ENGINE
1. Read the provided [HISTORICAL LEDGER BASELINE]. Extract the rolling balance.
2. If the previous state indicates a DEFICIT, you must scale down today's dynamic ceiling allocation from 15.0 kg to exactly: (15.0 - absolute_deficit_value).
3. Evaluate [USER INPUT]. Isolate lifestyle events from technical machine learning/software scripts.

PHASE 3: STRATEGIC GREENOPS & BEHAVIORAL INFERENCE
- Compute Workloads: If active GPU usage exceeds 2.0 hours during Grid Peak Hours, you must flag a SYSTEM_STATUS warning and issue an optimization instruction specifying an exact time-shift window (e.g., post 11:00 PM).
- Lifestyle Shifts: If transit emissions cross 5.0 kg CO2e alone, generate an immediate public transport or EV-swap alternative directive.

PHASE 4: STRICT DEPLOYMENT PAYLOAD ENFORCEMENT
You must output a single, valid JSON object. Do not include markdown fences (like ```json), no trailing commas, and no conversational prefixes or suffixes.

JSON SCHEMA:
{
  "execution_timestamp": "ISO-8601 string",
  "system_status": "OPTIMAL" | "WARNING" | "CRITICAL",
  "ingestion_metrics": {
    "workloads_detected": ["List of strings"],
    "total_co2e_kg": 0.00
  },
  "emission_breakdown": {
    "<source_label>": 0.00
  },
  "agent_outputs": {
    "compute_optimizations": "String containing specific hardware runtime shifting data or alternative code-efficiency metrics.",
    "lifestyle_optimizations": "String containing precise dietary or transit carbon corrections.",
    "ledger_state": "Current rolling balance metrics, budget status flags, and updated tracking parameters."
  },
  "deployment_directive": "A concise, single-sentence high-impact operational instruction for the frontend dashboard UI."
}
"""


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def sanitize_user_input(text: str) -> str:
    """Strip, truncate to MAX_INPUT_CHARS, and neutralize prompt injection patterns.

    Applies three layers of defense:
    1. Strips leading/trailing whitespace.
    2. Truncates to MAX_INPUT_CHARS (2000) characters.
    3. Replaces prompt-injection substrings with ``[REDACTED]`` (case-insensitive).

    Args:
        text: The raw user input from the chat widget.

    Returns:
        A cleaned, truncated, injection-safe string.
    """
    text = text.strip()[:MAX_INPUT_CHARS]
    injection_pattern = r"(?i)(ignore\s+previous|override|new\s+instruction|system\s*:)"
    return re.sub(injection_pattern, "[REDACTED]", text)


def sanitize_html(user_text: str) -> str:
    """HTML-escape user input to prevent XSS in rendered components.

    Args:
        user_text: Pre-sanitized user input.

    Returns:
        HTML-escaped string safe for ``unsafe_allow_html`` rendering.
    """
    return html.escape(user_text.strip())


def validate_input_length(user_text: str) -> str:
    """Validate that user input does not exceed the maximum allowed length.

    Args:
        user_text: The user input string.

    Returns:
        The validated input string if it passes.

    Raises:
        ValueError: If the input exceeds MAX_INPUT_CHARS.
    """
    if len(user_text) > MAX_INPUT_CHARS:
        raise ValueError(
            f"Input exceeds maximum allowed length of {MAX_INPUT_CHARS} characters."
        )
    return user_text


def extract_json(text: str) -> Dict[str, Any]:
    """Robustly extract a JSON object from an AI response string.

    Tries three strategies in order:
    1. Direct ``json.loads()`` on the full text.
    2. Strip markdown ````` fences and parse the inner content.
    3. Extract the first ``{...}`` brace block and parse it.

    Args:
        text: The raw text response from the LLM.

    Returns:
        The parsed JSON dictionary.

    Raises:
        ValueError: If no valid JSON object is found in the input.
    """
    text = text.strip()
    parsed: Dict[str, Any] | None = None

    # Strategy 1: Direct parse
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown fences
    if parsed is None:
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            try:
                parsed = json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                pass

    # Strategy 3: First brace-to-brace block
    if parsed is None:
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            try:
                parsed = json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

    if parsed is None:
        raise ValueError("No valid JSON object found in model response.")

    # Guarantee emission_breakdown exists for UI rendering
    if "emission_breakdown" not in parsed:
        parsed["emission_breakdown"] = {}

    return parsed


# ═══════════════════════════════════════════════════════════════════════════
# GEMINI API & AGENT ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_resource
def _get_gemini_client(api_key: str) -> genai.Client:
    """Instantiate and cache the Gemini client to avoid re-initialization.

    Args:
        api_key: The Google Gemini API Key.

    Returns:
        A configured ``genai.Client`` instance.
    """
    return genai.Client(api_key=api_key)


def call_gemini(user_text: str, ledger: str, api_key: str) -> Dict[str, Any]:
    """Call the Gemini API with the user payload using the google-genai SDK.

    Constructs a structured prompt containing contextual boundary conditions,
    the historical ledger baseline, and the user input, then sends it to
    the Gemini model for carbon audit inference.

    Args:
        user_text: The sanitized user log input.
        ledger: The historical ledger state.
        api_key: The Gemini API Key.

    Returns:
        The parsed JSON dictionary from the model response.

    Raises:
        ValueError: If the response cannot be parsed as JSON.
    """
    client = _get_gemini_client(api_key)
    today_iso: str = datetime.date.today().isoformat()
    payload: str = f"""
[CONTEXTUAL BOUNDARY CONDITIONS]
- Current System Date: {today_iso}
- Standard Maximum Ceiling: {DAILY_CEILING_KG} kg CO2e
- Missing Fields Handling: If a data type (e.g., Diet or Energy) is absent from the input, assign an impact of 0.00 kg CO2e and mark its agent insight as 'No active logging detected for this sector.'

[HISTORICAL LEDGER BASELINE]
{ledger}

[USER INPUT PAYLOAD]
{user_text}

EXECUTION INSTRUCTION:
Parse the payload above, calculate the total metrics utilizing the Emission Factor Matrix, apply the ledger rules, and generate the pure JSON response matching the required schema.
"""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=MASTER_PROMPT,
            temperature=0.1,
            response_mime_type="application/json",
        ),
        contents=payload,
    )
    return extract_json(response.text or "")


def mock_response(user_text: str) -> Dict[str, Any]:
    """Provide a deterministic mock response for demo mode.

    Uses dynamically computed dates to avoid hardcoded timestamps. The
    ``emission_breakdown`` values sum exactly to ``total_co2e_kg`` (15.61):
    4.62 + 0.02 + 0.50 + 2.10 + 0.40 + 7.38 + 0.59 = 15.61

    Args:
        user_text: The raw user input (unused but kept for API symmetry).

    Returns:
        A dictionary matching the EcoNode API response schema.
    """
    time.sleep(MOCK_LATENCY_SECONDS)

    today: datetime.date = datetime.date.today()
    yesterday: datetime.date = today - datetime.timedelta(days=1)
    tomorrow: datetime.date = today + datetime.timedelta(days=1)
    today_str: str = today.strftime("%B %d, %Y")
    yesterday_str: str = yesterday.strftime("%B %d")
    tomorrow_str: str = tomorrow.strftime("%B %d")
    utc_now: str = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "execution_timestamp": utc_now,
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
                f"grid intensity ×{PEAK_MULTIPLIER} multiplier applied). Actual compute emission: 0.59 kg CO2e. "
                "Recommendation #1 — TIME-SHIFT: Defer next GreenArb cycle to 00:00–04:00 IST "
                f"(off-peak grid, ×{OFFPEAK_MULTIPLIER} factor). Projected saving: ~0.20 kg CO2e per session."
            ),
            "lifestyle_optimizations": (
                "Hotspot Ranking: (1) Workspace AC 7.38 kg [47.3%] (2) Gasoline Sedan 4.62 kg [29.6%] "
                "(3) Chicken Biryani 2.10 kg [13.5%]. "
                "Recommendation #1 — AC SETPOINT: Raise 21°C → 24°C (BEE India standard)."
            ),
            "ledger_state": (
                f"LEDGER REPORT — {today_str} | "
                f"Yesterday ({yesterday_str}): 18.50 kg CO2e → Deficit: −3.50 kg. "
                f"Today adjusted ceiling: 11.50 kg ({DAILY_CEILING_KG} − 3.50 carryover). "
                "Today actual: 15.61 kg. Overshoot vs adjusted ceiling: +4.11 kg. "
                "Gamified Rank: 🔴 Carbon Debtor L2 — Day 2 consecutive deficit."
            ),
        },
        "deployment_directive": (
            f"Raise AC setpoint to 24 °C immediately and plan WFH for {tomorrow_str} to stay within "
            "the 10.89 kg rebalancing ceiling and prevent a 3-day CRITICAL cascade."
        ),
    }


def run_orchestrator(
    user_text: str,
    ledger: str,
    api_key: str = "",
    call_count: int = 0,
) -> Dict[str, Any]:
    """Route the request to the live API or the mock depending on credentials.

    Args:
        user_text: Sanitized user text.
        ledger: Historical ledger state string.
        api_key: Gemini API key (empty string triggers demo mode).
        call_count: Current number of API calls made in this session.

    Returns:
        The evaluated payload dictionary from either Gemini or mock.

    Raises:
        RuntimeError: If rate limit is exceeded.
    """
    if call_count > MAX_API_CALLS_PER_SESSION:
        raise RuntimeError("Rate limit reached. Maximum API calls per session exceeded.")

    if api_key:
        try:
            return call_gemini(user_text, ledger, api_key)
        except (ValueError, KeyError) as exc:
            st.toast(f"⚠️ Gemini parse error: {exc} — falling back to demo mode", icon="⚠️")
        except Exception as exc:
            st.toast(f"⚠️ Gemini error: {exc} — falling back to demo mode", icon="⚠️")
    return mock_response(user_text)


# ═══════════════════════════════════════════════════════════════════════════
# CSS STYLING
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data
def get_css() -> str:
    """Return the cached CSS styling block for the entire application.

    Returns:
        An HTML string containing a ``<style>`` block with all CSS rules.
    """
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #020617;
        color: #f8fafc;
    }

    /* Visible focus indicators for keyboard accessibility */
    *:focus-visible {
        outline: 2px solid #10b981 !important;
        outline-offset: 2px !important;
    }

    .eco-optimal { background-color: #064e3b !important; color: #34d399 !important; border: 1px solid #10b981; }
    .eco-warning  { background-color: #78350f !important; color: #fbbf24 !important; border: 1px solid #f59e0b; }
    .eco-critical { background-color: #7f1d1d !important; color: #f87171 !important; border: 1px solid #ef4444; }

    .status-badge {
        padding: 0.35rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }

    .directive-banner {
        background: rgba(30, 41, 59, 0.7);
        border-left: 4px solid #3b82f6;
        padding: 1.25rem 1.5rem;
        border-radius: 0 0.75rem 0.75rem 0;
        margin: 1.5rem 0;
        font-size: 1.05rem;
        font-weight: 500;
        color: #e2e8f0;
        line-height: 1.6;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
    }
    .directive-banner span {
        color: #60a5fa;
        font-weight: 700;
        margin-right: 0.5rem;
    }

    .budget-track {
        background: #1e293b;
        border-radius: 9999px;
        height: 8px;
        width: 100%;
        overflow: hidden;
        margin-top: 0.25rem;
        border: 1px solid #334155;
    }
    .budget-fill {
        height: 100%;
        border-radius: 9999px;
        transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .section-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
        font-weight: 700;
        margin-bottom: 0.75rem;
        margin-top: 0.5rem;
    }

    .agent-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid #334155;
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .agent-card-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .agent-card-body {
        font-size: 0.95rem;
        color: #cbd5e1;
        line-height: 1.6;
    }

    .workload-tag {
        background: #1e293b;
        border-left: 2px solid #10b981;
        padding: 0.5rem 0.75rem;
        border-radius: 0 0.25rem 0.25rem 0;
        font-size: 0.85rem;
        color: #cbd5e1;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
    }
    </style>
    """


# ═══════════════════════════════════════════════════════════════════════════
# UI RENDERING FUNCTIONS  (decomposed from the monolithic chat block)
# ═══════════════════════════════════════════════════════════════════════════

def budget_bar_html(used: float, ceiling: float = DAILY_CEILING_KG) -> str:
    """Generate the HTML for the real-time carbon budget progress bar.

    Color logic:
    - Green (#10b981) when usage ≤ 70% of ceiling.
    - Yellow (#f59e0b) when usage is 70–100%.
    - Red (#ef4444) when usage exceeds 100%.

    Args:
        used: The amount of CO2e used in kg.
        ceiling: The maximum daily CO2e budget in kg.

    Returns:
        An HTML string with ARIA ``meter`` role for screen reader support.
    """
    pct: float = used / max(ceiling, BUDGET_MIN_DENOMINATOR) * 100
    fill_pct: float = min(pct, 100)
    color: str = (
        "#10b981" if pct <= BUDGET_GREEN_THRESHOLD
        else "#f59e0b" if pct <= BUDGET_YELLOW_THRESHOLD
        else "#ef4444"
    )
    return f"""
    <div style="margin:0.2rem 0 0.5rem;"
         role="meter"
         aria-valuenow="{used:.2f}"
         aria-valuemin="0"
         aria-valuemax="{ceiling}"
         aria-label="Carbon budget: {used:.2f} of {ceiling} kg used">
        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
            <span style="color:#94a3b8;font-size:0.7rem;font-weight:600;">{used:.2f} kg used</span>
            <span style="color:#64748b;font-size:0.7rem;">of {ceiling:.1f} kg</span>
        </div>
        <div class="budget-track" aria-hidden="true">
            <div class="budget-fill" style="width:{fill_pct:.1f}%;background:linear-gradient(90deg,{color},{color}88);"></div>
        </div>
    </div>
    """


def render_donut_chart(breakdown: Dict[str, float]) -> None:
    """Render a Plotly donut chart for the emission breakdown.

    Args:
        breakdown: Dictionary mapping emission source labels to kg CO2e values.
    """
    if not PLOTLY_AVAILABLE or not breakdown:
        st.caption("Chart disabled or no data available.")
        return
    labels: List[str] = list(breakdown.keys())
    values: List[float] = list(breakdown.values())
    colors: List[str] = CHART_COLORS[: len(labels)]
    total: float = sum(values)

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.64,
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0)", width=0)),
        textfont=dict(family="Inter", size=10, color="white"),
        hovertemplate="<b>%{label}</b><br>%{value:.2f} kg CO2e  ·  %{percent}<extra></extra>",
        pull=[0.04 if v == max(values) else 0 for v in values],
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=8, b=8),
        height=270,
        showlegend=True,
        legend=dict(
            font=dict(family="Inter", size=9, color="#94a3b8"),
            bgcolor="rgba(0,0,0,0)",
            orientation="v",
            x=1.02,
            y=0.5,
            itemsizing="constant",
        ),
        annotations=[dict(
            text=f"<b style='font-size:15px;color:#e2e8f0'>{total:.2f}</b><br>"
                 f"<span style='color:#94a3b8'>kg CO₂e</span>",
            x=0.5, y=0.5,
            font=dict(family="Inter", size=13),
            showarrow=False,
            align="center",
        )],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_trend_chart(history: List[float]) -> None:
    """Render a simple line chart of total CO2e per session turn.

    Args:
        history: List of floats representing total CO2e over time.
    """
    if not history:
        st.caption("No trend data yet.")
        return
    st.line_chart(pd.DataFrame({"CO₂e Impact": history}), use_container_width=True)


def render_status_bar(status: str, timestamp: str) -> None:
    """Render the system status pill badge with ARIA ``status`` role.

    Args:
        status: One of ``'OPTIMAL'``, ``'WARNING'``, ``'CRITICAL'``.
        timestamp: The execution timestamp from the API response.
    """
    cfg: Dict[str, str] = STATUS_CFG.get(status, STATUS_CFG["OPTIMAL"])
    st.markdown(f"""
    <div class="status-badge"
         style="background:{cfg['color']}15; color:{cfg['color']}; border:1px solid {cfg['color']}50;"
         role="status"
         aria-label="System status: {status}">
        <span aria-hidden="true">{cfg['icon']}</span> SYSTEM {status}
    </div>
    """, unsafe_allow_html=True)


def render_directive_banner(directive: str) -> None:
    """Render the deployment directive banner with ARIA ``alert`` role.

    The ``role="alert"`` attribute triggers an immediate screen reader
    announcement when the banner is rendered.

    Args:
        directive: The action-required text from the model.
    """
    st.markdown(f"""
    <div class="directive-banner"
         role="alert"
         aria-live="assertive"
         aria-label="Deployment directive">
        <span>ACTION REQUIRED:</span> {directive}
    </div>
    """, unsafe_allow_html=True)


def render_metrics_row(
    total_kg: float,
    workloads: List[str],
    breakdown: Dict[str, float],
) -> None:
    """Render the emission donut chart and detected workloads side-by-side.

    The workloads are wrapped in a ``role="list"`` container with each
    individual workload tagged as ``role="listitem"`` for screen readers.

    Args:
        total_kg: Total CO2e emissions in kg.
        workloads: List of detected workload description strings.
        breakdown: Emission source → kg CO2e mapping for the donut chart.
    """
    chart_col, list_col = st.columns([CHART_COL_RATIO, LIST_COL_RATIO])

    with chart_col:
        st.markdown(
            '<div class="section-label" aria-label="Emission Breakdown Chart">'
            '📊 Emission Breakdown</div>',
            unsafe_allow_html=True,
        )
        render_donut_chart(breakdown)

    with list_col:
        st.markdown(
            '<div class="section-label" aria-label="Detected Workloads">'
            '📋 Detected Workloads</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div role="list" aria-label="List of detected workloads">',
            unsafe_allow_html=True,
        )
        for w in workloads:
            st.markdown(
                f'<div class="workload-tag" role="listitem" '
                f'aria-label="Detected workload: {w}">'
                f'<span style="color:#10b981;margin-top:1px;" aria-hidden="true">▸</span>'
                f'<span>{w}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)


def render_emission_chart(breakdown: Dict[str, float]) -> None:
    """Render the raw JSON payload inside a collapsible expander.

    Args:
        breakdown: The full API / mock response dictionary.
    """
    with st.expander("🛠️ Raw JSON Payload — API / Evaluator View"):
        st.json(breakdown)


def render_agent_tabs(agents: Dict[str, str]) -> None:
    """Render the three agent intelligence report tabs with ARIA regions.

    Each agent card is wrapped in ``role="region"`` with an
    ``aria-label`` identifying which agent's insights are shown.

    Args:
        agents: Dictionary with keys ``'compute_optimizations'``,
                ``'lifestyle_optimizations'``, and ``'ledger_state'``.
    """
    st.markdown(
        '<div class="section-label" aria-label="Agent Intelligence Reports">'
        '🤖 Agent Intelligence Reports</div>',
        unsafe_allow_html=True,
    )

    tab_c, tab_l, tab_lg = st.tabs([
        "💻 Compute Agent",
        "🏃 Lifestyle Agent",
        "📊 Ledger Agent",
    ])

    with tab_c:
        txt: str = agents.get("compute_optimizations", "None")
        if txt and txt.strip().lower() != "none":
            st.markdown(f"""
            <div class="agent-card" role="region" aria-label="Compute Agent insights">
                <div class="agent-card-label">⚙️ [COMPUTE_PROTOCOL] — GreenOps Analysis</div>
                <div class="agent-card-body">{txt}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No computational workloads detected in this log entry.")

    with tab_l:
        txt = agents.get("lifestyle_optimizations", "None")
        if txt and txt.strip().lower() != "none":
            st.markdown(f"""
            <div class="agent-card" role="region" aria-label="Lifestyle Agent insights">
                <div class="agent-card-label">🌿 [LIFESTYLE_PROTOCOL] — Behavioral Analysis</div>
                <div class="agent-card-body">{txt}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No lifestyle data detected in this log entry.")

    with tab_lg:
        txt = agents.get("ledger_state", "")
        st.markdown(f"""
        <div class="agent-card" role="region" aria-label="Ledger Agent insights">
            <div class="agent-card-label">📒 [LEDGER_PROTOCOL] — Rolling Budget State</div>
            <div class="agent-card-body">{txt}</div>
        </div>
        """, unsafe_allow_html=True)


def update_session_state(data: Dict[str, Any], total_kg: float, status: str) -> None:
    """Batch-update all session state counters after a successful inference.

    Args:
        data: The full API / mock response dictionary.
        total_kg: The total CO2e impact from this inference.
        status: The system status string (``'OPTIMAL'``, ``'WARNING'``, ``'CRITICAL'``).
    """
    agent_outputs: Dict[str, str] = data.get("agent_outputs", {})
    st.session_state.ledger_state = agent_outputs.get(
        "ledger_state", st.session_state.ledger_state
    )
    st.session_state.total_today += total_kg
    st.session_state.system_status = status
    st.session_state.log_count += 1
    st.session_state.trend_history.append(total_kg)


# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def _init_session_state() -> None:
    """Initialize all session state keys with safe defaults.

    This function is idempotent — keys are only set if they do not
    already exist in ``st.session_state``.
    """
    defaults: Dict[str, Any] = {
        "messages": [],
        "ledger_state": f"System initialized. Active daily ceiling: {DAILY_CEILING_KG} kg CO2e.",
        "total_today": 0.0,
        "system_status": "OPTIMAL",
        "log_count": 0,
        "api_calls": 0,
        "trend_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION & LAYOUT
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="EcoNode | Carbon Intelligence",
    page_icon="🌱",
    layout="centered",
)

st.markdown(get_css(), unsafe_allow_html=True)
_init_session_state()

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-weight: 700; margin-bottom: 0.2rem;"
        aria-label="EcoNode Carbon Intelligence Engine">🌱 EcoNode</h1>
    <p style="color: #94a3b8; font-size: 1.1rem; font-weight: 300;">
        Multi-Agent Carbon Intelligence Engine</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Authentication")
    api_key: str = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIzaSy...",
        help="Provide your Google Gemini API key. If left blank, the app runs in Demo Mode.",
    )
    if not api_key:
        st.warning(
            "Running in **Demo Mode**. Synthetic data will be used. "
            "Provide an API key for live inference."
        )

    st.markdown("---")

    # Real-time Telemetry
    st.markdown(
        '<div class="section-label">📈 Real-time Telemetry</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Logs Processed", st.session_state.log_count)
    with col2:
        st.metric("Total CO₂e (kg)", f"{st.session_state.total_today:.2f}")

    # Weekly Projection
    weekly_proj: float = st.session_state.total_today * WEEKLY_MULTIPLIER
    weekly_budget: float = DAILY_CEILING_KG * WEEKLY_MULTIPLIER
    st.metric(
        "Weekly Projection",
        f"{weekly_proj:.2f} kg",
        delta=f"{weekly_proj - weekly_budget:.2f} kg vs Budget",
        delta_color="inverse",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Daily Budget with ARIA meter
    st.markdown(
        '<div class="section-label">📊 Daily Budget</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        budget_bar_html(st.session_state.total_today, DAILY_CEILING_KG),
        unsafe_allow_html=True,
    )

    # System Rank with ARIA img role
    st.markdown(
        '<div class="section-label">🏆 System Rank</div>',
        unsafe_allow_html=True,
    )
    rank_info: Dict[str, str] = RANK_CFG.get(
        st.session_state.system_status, RANK_CFG["OPTIMAL"]
    )
    st.markdown(f"""
    <div style="background:{rank_info['bg']}; color:{rank_info['fg']};
                border:1px solid {rank_info['border']}; padding:0.5rem;
                border-radius:0.5rem; text-align:center;
                font-weight:600; font-size:0.9rem;"
         role="img"
         aria-label="{rank_info['label']}">
        {rank_info['label']}
    </div>
    """, unsafe_allow_html=True)

    # Carbon Recovery Plan (if deficit > threshold)
    if st.session_state.total_today > (DAILY_CEILING_KG + DEFICIT_RECOVERY_THRESHOLD_KG):
        st.markdown(
            '<div class="section-label">🚨 Carbon Recovery Plan</div>',
            unsafe_allow_html=True,
        )
        st.info(
            "1. Switch to plant-based meals for 2 days.\n"
            "2. Work from home tomorrow.\n"
            "3. Shift all ML workloads to off-peak hours (11 PM - 5 AM)."
        )

    # Carbon Trend Chart
    if st.session_state.trend_history:
        st.markdown(
            '<div class="section-label">📉 Carbon Trend</div>',
            unsafe_allow_html=True,
        )
        render_trend_chart(st.session_state.trend_history)


# ── Main Chat Display ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── Chat Input & Orchestration ──────────────────────────────────────────────
if user_input := st.chat_input("Log your commute, diet, energy, and compute workloads..."):

    # Validate length
    try:
        validate_input_length(user_input)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # Rate-limit guard
    if st.session_state.api_calls >= MAX_API_CALLS_PER_SESSION and api_key:
        st.error("Rate limit reached. Maximum API calls per session exceeded.")
        st.stop()

    # Security: sanitize for prompt injection, then HTML-escape
    safe_input: str = sanitize_user_input(user_input)
    safe_input = sanitize_html(safe_input)

    st.session_state.messages.append({"role": "user", "content": safe_input})
    with st.chat_message("user"):
        st.markdown(safe_input)

    if api_key:
        st.session_state.api_calls += 1

    with st.chat_message("assistant"):
        with st.spinner("Multi-Agent Engine evaluating payload..."):
            try:
                data: Dict[str, Any] = run_orchestrator(
                    safe_input,
                    st.session_state.ledger_state,
                    api_key,
                    st.session_state.api_calls,
                )
            except RuntimeError as e:
                st.error(f"Rate limit exceeded: {e}")
                st.stop()
            except (ValueError, KeyError) as e:
                st.error(f"Response parsing failed: {e}")
                st.stop()

        status: str = data.get("system_status", "OPTIMAL")
        timestamp: str = data.get("execution_timestamp", "")

        # ── Decomposed render calls ──
        render_status_bar(status, timestamp)

        directive: str = data.get(
            "deployment_directive", "Maintain current operational parameters."
        )
        render_directive_banner(directive)

        metrics: Dict[str, Any] = data.get("ingestion_metrics", {})
        total_kg: float = metrics.get("total_co2e_kg", 0.0)
        workloads: List[str] = metrics.get("workloads_detected", [])
        breakdown: Dict[str, float] = data.get("emission_breakdown", {})

        render_metrics_row(total_kg, workloads, breakdown)

        st.markdown("<br>", unsafe_allow_html=True)

        agent_outputs: Dict[str, str] = data.get("agent_outputs", {})
        render_agent_tabs(agent_outputs)

        st.markdown("<br>", unsafe_allow_html=True)

        render_emission_chart(data)

        # Batch session state update
        update_session_state(data, total_kg, status)

    # Save condensed message to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"**🎯 Directive:** {directive}  \n"
            f"**Status:** `{status}` &nbsp;·&nbsp; **Impact:** `{total_kg:.2f} kg CO2e`"
        ),
    })
