"""EcoNode main Streamlit entry point.

Run with: streamlit run app.py

This module composes the full EcoNode dashboard by wiring together
config constants, utility functions, agent orchestration, and the
ARIA-accessible UI rendering layer.
"""

__version__ = "2.1.0"

from typing import Any, Dict, List

import streamlit as st

from agents import run_orchestrator
from config import DAILY_CEILING_KG, MAX_API_CALLS_PER_SESSION, RANK_CFG, STATUS_CFG
from ui import budget_bar_html, get_css, render_donut_chart, render_trend_chart
from utils import sanitize_input, sanitize_user_input, validate_input_length

# ── Named Constants (extracted magic numbers) ───────────────────────────────
DEFICIT_RECOVERY_THRESHOLD_KG: float = 5.0
WEEKLY_MULTIPLIER: int = 7
CHART_COL_RATIO: float = 1.3
LIST_COL_RATIO: float = 1.0


# ── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="EcoNode | Carbon Intelligence",
    page_icon="🌱",
    layout="centered",
)

# Inject CSS
st.markdown(get_css(), unsafe_allow_html=True)


# ── Session State Initialization ────────────────────────────────────────────
def _init_session_state() -> None:
    """Initialize all session state keys with safe defaults.

    Ensures idempotent initialization — keys are only set if they
    do not already exist.
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


_init_session_state()


# ── Render Functions ────────────────────────────────────────────────────────

def render_status_bar(status: str, cfg: Dict[str, str]) -> None:
    """Render the system status pill badge with ARIA role.

    Args:
        status: One of 'OPTIMAL', 'WARNING', 'CRITICAL'.
        cfg: STATUS_CFG entry with 'icon' and 'color' keys.
    """
    st.markdown(f"""
    <div class="status-badge"
         style="background:{cfg['color']}15; color:{cfg['color']}; border:1px solid {cfg['color']}50;"
         role="status"
         aria-label="System status: {status}">
        <span aria-hidden="true">{cfg['icon']}</span> SYSTEM {status}
    </div>
    """, unsafe_allow_html=True)


def render_directive_banner(directive: str) -> None:
    """Render the deployment directive banner with ARIA alert role.

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

    Args:
        total_kg: Total CO2e emissions in kg.
        workloads: List of detected workload description strings.
        breakdown: Emission source → kg CO2e mapping.
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
        # Wrap workload items in a list container for screen readers
        st.markdown('<div role="list" aria-label="List of detected workloads">', unsafe_allow_html=True)
        for w in workloads:
            st.markdown(
                f'<div class="workload-tag" role="listitem" '
                f'aria-label="Detected workload: {w}">'
                f'<span style="color:#10b981;margin-top:1px;" aria-hidden="true">▸</span>'
                f'<span>{w}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)


def render_emission_chart(data: Dict[str, Any]) -> None:
    """Render the raw JSON payload inside a collapsible expander.

    Args:
        data: The full API / mock response dictionary.
    """
    with st.expander("🛠️ Raw JSON Payload — API / Evaluator View"):
        st.json(data)


def render_agent_tabs(agents: Dict[str, str]) -> None:
    """Render the three agent intelligence report tabs with ARIA regions.

    Args:
        agents: Dictionary with keys 'compute_optimizations',
                'lifestyle_optimizations', and 'ledger_state'.
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
        txt = agents.get("compute_optimizations", "None")
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
        status: The system status string ('OPTIMAL', 'WARNING', 'CRITICAL').
    """
    agent_outputs: Dict[str, str] = data.get("agent_outputs", {})
    st.session_state.ledger_state = agent_outputs.get(
        "ledger_state", st.session_state.ledger_state
    )
    st.session_state.total_today += total_kg
    st.session_state.system_status = status
    st.session_state.log_count += 1
    st.session_state.trend_history.append(total_kg)


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-weight: 700; margin-bottom: 0.2rem;" aria-label="EcoNode Carbon Intelligence Engine">🌱 EcoNode</h1>
    <p style="color: #94a3b8; font-size: 1.1rem; font-weight: 300;">Multi-Agent Carbon Intelligence Engine</p>
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
        st.warning("Running in **Demo Mode**. Synthetic data will be used. Provide an API key for live inference.")

    st.markdown("---")

    # Real-time Telemetry
    st.markdown('<div class="section-label">📈 Real-time Telemetry</div>', unsafe_allow_html=True)

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

    # Daily Budget with ARIA meter role
    st.markdown('<div class="section-label">📊 Daily Budget</div>', unsafe_allow_html=True)
    st.markdown(
        budget_bar_html(st.session_state.total_today, DAILY_CEILING_KG),
        unsafe_allow_html=True,
    )

    # System Rank with ARIA img role
    st.markdown('<div class="section-label">🏆 System Rank</div>', unsafe_allow_html=True)
    rank_info = RANK_CFG.get(st.session_state.system_status, RANK_CFG["OPTIMAL"])
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
        st.markdown('<div class="section-label">🚨 Carbon Recovery Plan</div>', unsafe_allow_html=True)
        st.info(
            "1. Switch to plant-based meals for 2 days.\n"
            "2. Work from home tomorrow.\n"
            "3. Shift all ML workloads to off-peak hours (11 PM - 5 AM)."
        )

    # Carbon Trend Chart
    if st.session_state.trend_history:
        st.markdown('<div class="section-label">📉 Carbon Trend</div>', unsafe_allow_html=True)
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
    safe_input = sanitize_input(safe_input)

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
        cfg: Dict[str, str] = STATUS_CFG.get(status, STATUS_CFG["OPTIMAL"])

        # ── Decomposed render calls ──
        render_status_bar(status, cfg)

        directive: str = data.get("deployment_directive", "Maintain current operational parameters.")
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
