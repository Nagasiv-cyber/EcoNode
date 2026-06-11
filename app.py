"""EcoNode main Streamlit entry point. Run with: streamlit run app.py"""

__version__ = "2.1.0"

import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EcoNode | Carbon Intelligence",
    page_icon="🌱",
    layout="centered"
)

from config import STATUS_CFG, RANK_CFG, DAILY_CEILING_KG, MAX_API_CALLS_PER_SESSION, MAX_INPUT_LENGTH
from utils import sanitize_input, validate_input_length
from agents import run_orchestrator
from ui import get_css, budget_bar_html, render_donut_chart, render_trend_chart

# Inject CSS
st.markdown(get_css(), unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ledger_state" not in st.session_state:
    st.session_state.ledger_state = f"System initialized. Active daily ceiling: {DAILY_CEILING_KG} kg CO2e."
if "total_today" not in st.session_state:
    st.session_state.total_today = 0.0
if "system_status" not in st.session_state:
    st.session_state.system_status = "OPTIMAL"
if "log_count" not in st.session_state:
    st.session_state.log_count = 0
if "api_calls" not in st.session_state:
    st.session_state.api_calls = 0
if "trend_history" not in st.session_state:
    st.session_state.trend_history = []

# Top Header
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-weight: 700; margin-bottom: 0.2rem;">🌱 EcoNode</h1>
    <p style="color: #94a3b8; font-size: 1.1rem; font-weight: 300;">Multi-Agent Carbon Intelligence Engine</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🔑 Authentication")
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIzaSy...",
        help="Provide your Google Gemini API key. If left blank, the app runs in Demo Mode."
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
    weekly_proj = st.session_state.total_today * 7
    st.metric("Weekly Projection", f"{weekly_proj:.2f} kg", delta=f"{weekly_proj - (DAILY_CEILING_KG*7):.2f} kg vs Budget", delta_color="inverse")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Daily Budget
    st.markdown('<div class="section-label">📊 Daily Budget</div>', unsafe_allow_html=True)
    st.markdown(budget_bar_html(st.session_state.total_today, DAILY_CEILING_KG), unsafe_allow_html=True)
    
    # System Rank
    st.markdown('<div class="section-label">🏆 System Rank</div>', unsafe_allow_html=True)
    rank_info = RANK_CFG.get(st.session_state.system_status, RANK_CFG["OPTIMAL"])
    st.markdown(f"""
    <div style="background:{rank_info['bg']}; color:{rank_info['fg']}; border:1px solid {rank_info['border']}; padding:0.5rem; border-radius:0.5rem; text-align:center; font-weight:600; font-size:0.9rem;">
        {rank_info['label']}
    </div>
    """, unsafe_allow_html=True)
    
    # Carbon Recovery Plan (if deficit > 5 kg)
    if st.session_state.total_today > (DAILY_CEILING_KG + 5.0):
        st.markdown('<div class="section-label">🚨 Carbon Recovery Plan</div>', unsafe_allow_html=True)
        st.info("1. Switch to plant-based meals for 2 days.\n2. Work from home tomorrow.\n3. Shift all ML workloads to off-peak hours (11 PM - 5 AM).")
    
    # Carbon Trend Chart
    if st.session_state.trend_history:
        st.markdown('<div class="section-label">📉 Carbon Trend</div>', unsafe_allow_html=True)
        render_trend_chart(st.session_state.trend_history)

# Main Chat Display
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input & Orchestration
if user_input := st.chat_input("Log your commute, diet, energy, and compute workloads..."):
    
    try:
        validate_input_length(user_input)
    except ValueError as e:
        st.error(str(e))
        st.stop()
        
    if st.session_state.api_calls >= MAX_API_CALLS_PER_SESSION and api_key:
        st.error("Rate limit reached. Maximum API calls per session exceeded.")
        st.stop()
        
    safe_input = sanitize_input(user_input)
    
    st.session_state.messages.append({"role": "user", "content": safe_input})
    with st.chat_message("user"):
        st.markdown(safe_input)
        
    if api_key:
        st.session_state.api_calls += 1

    with st.chat_message("assistant"):
        with st.spinner("Multi-Agent Engine evaluating payload..."):
            try:
                data = run_orchestrator(safe_input, st.session_state.ledger_state, api_key, st.session_state.api_calls)
            except Exception as e:
                st.error(f"Execution failed: {e}")
                st.stop()

        status = data.get("system_status", "OPTIMAL")
        cfg = STATUS_CFG.get(status, STATUS_CFG["OPTIMAL"])
        
        # Header Badge
        st.markdown(f"""
        <div class="status-badge" style="background:{cfg['color']}15; color:{cfg['color']}; border:1px solid {cfg['color']}50;" role="status" aria-label="System status: {status}">
            <span aria-hidden="true">{cfg['icon']}</span> SYSTEM {status}
        </div>
        """, unsafe_allow_html=True)
        
        # Directive
        directive = data.get("deployment_directive", "Maintain current operational parameters.")
        st.markdown(f"""
        <div class="directive-banner" role="alert" aria-live="assertive" aria-label="Deployment directive">
            <span>ACTION REQUIRED:</span> {directive}
        </div>
        """, unsafe_allow_html=True)
        
        metrics = data.get("ingestion_metrics", {})
        total_kg = metrics.get("total_co2e_kg", 0.0)
        workloads = metrics.get("workloads_detected", [])
        breakdown = data.get("emission_breakdown", {})
        agents = data.get("agent_outputs", {})

        chart_col, list_col = st.columns([1.3, 1])

        with chart_col:
            st.markdown('<div class="section-label" aria-label="Emission Breakdown Chart">📊 Emission Breakdown</div>', unsafe_allow_html=True)
            render_donut_chart(breakdown)

        with list_col:
            st.markdown('<div class="section-label" aria-label="Detected Workloads">📋 Detected Workloads</div>', unsafe_allow_html=True)
            for w in workloads:
                st.markdown(f'<div class="workload-tag" role="listitem" aria-label="Detected workload: {w}"><span style="color:#10b981;margin-top:1px;" aria-hidden="true">▸</span><span>{w}</span></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="section-label" aria-label="Agent Intelligence Reports">🤖 Agent Intelligence Reports</div>', unsafe_allow_html=True)

        tab_c, tab_l, tab_lg = st.tabs(["💻 Compute Agent", "🏃 Lifestyle Agent", "📊 Ledger Agent"])

        with tab_c:
            txt = agents.get("compute_optimizations", "None")
            if txt and txt.strip().lower() != "none":
                st.markdown(f"""
                <div class="agent-card" role="region" aria-label="Compute Agent analysis output">
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
                <div class="agent-card" role="region" aria-label="Lifestyle Agent analysis output">
                    <div class="agent-card-label">🌿 [LIFESTYLE_PROTOCOL] — Behavioral Analysis</div>
                    <div class="agent-card-body">{txt}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No lifestyle data detected in this log entry.")

        with tab_lg:
            txt = agents.get("ledger_state", "")
            st.markdown(f"""
            <div class="agent-card" role="region" aria-label="Ledger Agent analysis output">
                <div class="agent-card-label">📒 [LEDGER_PROTOCOL] — Rolling Budget State</div>
                <div class="agent-card-body">{txt}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("🛠️ Raw JSON Payload — API / Evaluator View"):
            st.json(data)

        # Update session state (batched)
        st.session_state.ledger_state  = agents.get("ledger_state", st.session_state.ledger_state)
        st.session_state.total_today  += total_kg
        st.session_state.system_status = status
        st.session_state.log_count    += 1
        st.session_state.trend_history.append(total_kg)

    # Save condensed message to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"**🎯 Directive:** {directive}  \n"
            f"**Status:** `{status}` &nbsp;·&nbsp; **Impact:** `{total_kg:.2f} kg CO2e`"
        ),
    })
