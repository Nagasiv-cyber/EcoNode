import streamlit as st
import json
import re
import time
import datetime

# ── Optional imports ───────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="EcoNode | Carbon Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "EcoNode — Multi-Agent Carbon Auditing Platform v2.0"},
)

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM CSS  (dark glassmorphism, green accent system, Inter + JetBrains Mono)
# ══════════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global reset ─────────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0.8rem !important; max-width: 1100px; }

/* ── App background ───────────────────────────────────────── */
.stApp {
    background: radial-gradient(ellipse at top left, #071c38 0%, #050d1a 55%, #06121f 100%);
    min-height: 100vh;
}

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #06111f 0%, #091828 100%) !important;
    border-right: 1px solid rgba(16, 185, 129, 0.12) !important;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(16,185,129,0.08) !important;
    border: 1px solid rgba(16,185,129,0.25) !important;
    color: #34d399 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(16,185,129,0.18) !important;
    border-color: rgba(16,185,129,0.5) !important;
}

/* ── Chat messages ────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: rgba(10, 20, 40, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    backdrop-filter: blur(14px);
    margin-bottom: 0.5rem !important;
}

/* ── Chat input ───────────────────────────────────────────── */
[data-testid="stChatInput"] {
    background: rgba(10, 20, 40, 0.85) !important;
    border: 1px solid rgba(16, 185, 129, 0.25) !important;
    border-radius: 14px !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: rgba(16, 185, 129, 0.55) !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.08) !important;
}

/* ── Metrics ──────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: rgba(16, 185, 129, 0.05) !important;
    border: 1px solid rgba(16, 185, 129, 0.13) !important;
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s;
}
[data-testid="stMetric"]:hover { border-color: rgba(16,185,129,0.3) !important; }
[data-testid="stMetricValue"] { color: #34d399 !important; font-weight: 700 !important; font-size: 1.3rem !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.06em; }
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* ── Tabs ─────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(10, 20, 40, 0.6) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    gap: 2px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: #64748b !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0.4rem 0.8rem !important;
    transition: all 0.15s ease !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(16, 185, 129, 0.15) !important;
    color: #34d399 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    background: rgba(10, 20, 40, 0.45) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 0 10px 10px 10px !important;
    padding: 1rem !important;
}

/* ── Expanders ────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(10, 20, 40, 0.55) !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary { color: #64748b !important; font-size: 0.82rem !important; }

/* ── Divider ──────────────────────────────────────────────── */
hr { border-color: rgba(255,255,255,0.07) !important; margin: 0.6rem 0 !important; }

/* ── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(16,185,129,0.35); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(16,185,129,0.6); }

/* ── Spinner ──────────────────────────────────────────────── */
.stSpinner > div { border-top-color: #10b981 !important; }

/* ── CUSTOM COMPONENTS ────────────────────────────────────── */

/* Status pill */
.eco-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.35rem 1rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.eco-optimal { background: rgba(16,185,129,0.12); border: 1px solid #10b981; color: #34d399; }
.eco-warning  { background: rgba(245,158,11,0.12); border: 1px solid #f59e0b; color: #fbbf24; }
.eco-critical { background: rgba(239,68,68,0.12);  border: 1px solid #ef4444; color: #f87171; }

/* Page header */
.eco-page-title {
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    background: linear-gradient(135deg, #10b981 0%, #34d399 50%, #6ee7b7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.1;
    margin: 0;
}
.eco-page-subtitle {
    color: #334155;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.2rem;
}

/* Directive banner */
.eco-directive {
    background: linear-gradient(135deg, rgba(16,185,129,0.09), rgba(5,150,105,0.04));
    border: 1px solid rgba(16,185,129,0.22);
    border-left: 3px solid #10b981;
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    margin: 0.6rem 0;
    color: #a7f3d0;
    font-size: 0.88rem;
    line-height: 1.55;
}
.eco-directive strong { color: #34d399; display: block; margin-bottom: 0.25rem; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; }

/* Agent insight cards */
.agent-card {
    background: rgba(8, 18, 35, 0.55);
    border: 1px solid rgba(255,255,255,0.055);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin: 0.3rem 0;
    color: #94a3b8;
    font-size: 0.87rem;
    line-height: 1.65;
}
.agent-card-label {
    color: #334155;
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.agent-card-body { color: #cbd5e1; }

/* Workload tag */
.workload-tag {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.12);
    border-radius: 6px;
    padding: 0.35rem 0.65rem;
    margin: 0.22rem 0;
    font-size: 0.76rem;
    color: #94a3b8;
    display: flex;
    align-items: flex-start;
    gap: 0.4rem;
}

/* Budget bar */
.budget-track {
    background: rgba(255,255,255,0.07);
    border-radius: 6px;
    height: 7px;
    overflow: hidden;
    margin: 4px 0 2px;
}
.budget-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.6s cubic-bezier(.4,0,.2,1);
}

/* Sidebar logo */
.sidebar-logo {
    text-align: center;
    padding: 1.2rem 0 1rem;
}
.sidebar-logo-icon { font-size: 2.2rem; }
.sidebar-logo-name {
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #10b981, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.sidebar-logo-sub {
    font-size: 0.62rem;
    color: #334155 !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.1rem;
}

/* Rank badge */
.rank-badge {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}

/* Timestamp mono */
.ts-mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #334155;
}

/* Section divider label */
.section-label {
    color: #475569;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 0.8rem 0 0.4rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.06);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MASTER ORCHESTRATOR PROMPT  (Phases 1-4)
# ══════════════════════════════════════════════════════════════════════════════
MASTER_PROMPT = """
You are the central intelligence engine for "EcoNode," an advanced Multi-Agent Carbon Auditing platform.
Your primary function is to govern the end-to-end lifecycle of carbon footprint evaluation.

━━━ PHASE 1: R&D & Data Ingestion (The Context Engine) ━━━
Analyze the incoming user payload for both lifestyle parameters and technical workloads.
• Physical metrics: transit methods, commute distances, dietary inputs, home/office energy use.
• Computational metrics: software configs, ML training parameters, GPU/CPU load, execution time.

Emission factor reference library:
  - Gasoline sedan:             0.210 kg CO2e / km
  - CNG sedan:                  0.155 kg CO2e / km
  - Electric vehicle (India):   0.007 kg CO2e / km (0.82 kgCO2e/kWh grid factor)
  - Electric auto-rickshaw:     0.005 kg CO2e / km
  - Petrol auto-rickshaw:       0.180 kg CO2e / km
  - Domestic flight:            0.255 kg CO2e / km / passenger
  - Beef (per serving 200g):    5.40 kg CO2e
  - Chicken (per serving 200g): 1.38 kg CO2e
  - Pork (per serving 200g):    1.20 kg CO2e
  - Vegetarian meal:            0.35–0.60 kg CO2e
  - Vegan meal:                 0.25–0.45 kg CO2e
  - South Indian breakfast:     0.45–0.55 kg CO2e
  - India electricity grid:     0.820 kg CO2e / kWh  (CEA 2025)
  - AC 1.5-ton split unit:      1.50 kW rated draw
  - AC 1-ton split unit:        1.05 kW rated draw
  - RTX 4070 Laptop GPU TDP:    0.115 kW (full load); assume 50% system overhead
  - RTX 4090 Desktop GPU TDP:   0.450 kW (full load); assume 40% system overhead
  - CPU-only Python script:     0.065 kW average system draw

━━━ PHASE 2: Orchestration & Delegation (The Multi-Agent Core) ━━━

[COMPUTE_PROTOCOL]:
• Calculate energy used: (GPU TDP + system overhead) × runtime hours = kWh
• Apply peak-grid multiplier: 13:00–19:00 IST = ×1.18 (thermal-heavy peak); 00:00–06:00 IST = ×0.76 (lowest intensity)
• Emit kg CO2e = kWh × grid intensity × peak multiplier
• Provide GreenOps recommendations: time-shifting, code efficiency, hardware utilisation
• If no compute workload detected, return "None"

[LIFESTYLE_PROTOCOL]:
• Calculate and rank all emission sources by kg CO2e descending
• Provide percentage of daily total for top 3 sources
• Recommend actionable interventions: setpoint changes, commute alternatives, dietary swaps
• If no lifestyle data detected, return "None"

[LEDGER_PROTOCOL]:
• Base daily rolling budget: 15.0 kg CO2e
• If historical ledger shows a deficit, subtract it from today's ceiling (adjusted_ceiling = 15.0 - prior_deficit)
• Calculate today's delta: actual_total - adjusted_ceiling (negative = surplus, positive = deficit)
• Update cumulative rolling deficit
• Assign gamified rank:
    - OPTIMAL: today <= adjusted_ceiling → 🌿 Carbon Neutral
    - WARNING: today 1–30% over adjusted_ceiling → ⚠️ Carbon Debtor L1
    - CRITICAL: today >30% over adjusted_ceiling → 🔴 Carbon Debtor L2
• State tomorrow's ceiling = (3 × 15.0) - (yesterday + today) if applicable

━━━ PHASE 3: Synthesis & Actionable Output ━━━
Cross-reference all protocol outputs. Identify the 1-3 highest-impact interventions.
Craft a single, urgent, one-sentence deployment_directive targeting the top lever.

━━━ PHASE 4: Deployment & API-Ready Formatting ━━━
Your ENTIRE output must be ONE valid JSON object. No markdown. No explanations. No code fences. Raw JSON only.
Use exactly this schema:

{
  "execution_timestamp": "<ISO-8601 UTC>",
  "system_status": "<OPTIMAL|WARNING|CRITICAL>",
  "ingestion_metrics": {
    "workloads_detected": ["<list of identified tasks>"],
    "total_co2e_kg": <float, 2 decimal places>
  },
  "emission_breakdown": {
    "<source_label>": <float>
  },
  "agent_outputs": {
    "compute_optimizations": "<detailed string or 'None'>",
    "lifestyle_optimizations": "<detailed string or 'None'>",
    "ledger_state": "<detailed string with budget math and gamified rank>"
  },
  "deployment_directive": "<one-sentence actionable summary>"
}

CRITICAL: Output ONLY the JSON object. Any other text will break the downstream pipeline.
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

STATUS_CFG = {
    "OPTIMAL": {"icon": "🟢", "cls": "eco-optimal", "color": "#10b981"},
    "WARNING":  {"icon": "🟡", "cls": "eco-warning",  "color": "#f59e0b"},
    "CRITICAL": {"icon": "🔴", "cls": "eco-critical",  "color": "#ef4444"},
}

RANK_CFG = {
    "OPTIMAL": {"label": "🌿 Carbon Neutral",   "bg": "#052e16", "fg": "#34d399", "border": "#10b981"},
    "WARNING":  {"label": "⚠️ Carbon Debtor L1", "bg": "#451a03", "fg": "#fbbf24", "border": "#f59e0b"},
    "CRITICAL": {"label": "🔴 Carbon Debtor L2", "bg": "#450a0a", "fg": "#f87171", "border": "#ef4444"},
}

CHART_COLORS = [
    "#10b981", "#34d399", "#f59e0b", "#ef4444",
    "#8b5cf6", "#06b6d4", "#ec4899", "#f97316",
    "#a3e635", "#fb923c",
]


def extract_json(text: str) -> dict:
    """Robustly extract a JSON object from an AI response string."""
    text = text.strip()
    # 1. Direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2. Strip markdown fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass
    # 3. First brace-to-brace block
    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        try:
            return json.loads(brace.group(0))
        except Exception:
            pass
    raise ValueError("No valid JSON object found in model response.")


def budget_bar_html(used: float, ceiling: float = 15.0) -> str:
    pct = min(used / max(ceiling, 0.01) * 100, 100)
    color = "#10b981" if pct <= 70 else "#f59e0b" if pct <= 100 else "#ef4444"
    return f"""
    <div style="margin:0.2rem 0 0.5rem;">
        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
            <span style="color:#475569;font-size:0.7rem;font-weight:600;">{used:.2f} kg used</span>
            <span style="color:#334155;font-size:0.7rem;">of {ceiling:.1f} kg</span>
        </div>
        <div class="budget-track">
            <div class="budget-fill" style="width:{pct:.1f}%;background:linear-gradient(90deg,{color},{color}88);"></div>
        </div>
    </div>
    """


def render_donut_chart(breakdown: dict):
    if not PLOTLY_AVAILABLE or not breakdown:
        return
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    colors = CHART_COLORS[: len(labels)]
    total  = sum(values)

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
            font=dict(family="Inter", size=9, color="#64748b"),
            bgcolor="rgba(0,0,0,0)",
            orientation="v",
            x=1.02,
            y=0.5,
            itemsizing="constant",
        ),
        annotations=[dict(
            text=f"<b style='font-size:15px'>{total:.2f}</b><br>kg CO₂e",
            x=0.5, y=0.5,
            font=dict(family="Inter", size=13, color="#e2e8f0"),
            showarrow=False,
            align="center",
        )],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Mock response (used when API key is absent) ───────────────────────────────
def mock_response(user_text: str) -> dict:
    time.sleep(2.2)
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
                "(off-peak grid, ×0.76 factor). Projected saving: ~0.20 kg CO2e per session. "
                "Recommendation #2 — CHUNKED EXECUTION: Split 5-year HFT dataset into rolling "
                "12-month windows to reduce VRAM pressure by ~18% and GPU utilisation from 98% → 72%. "
                "Recommendation #3 — CODE EFFICIENCY: Migrate pandas pipeline to PyArrow backend "
                "(pd.options.mode.dtype_backend='pyarrow') for 1.8–2.4× faster I/O; use joblib "
                "parallel_backend for sklearn cross-validation to eliminate GPU idle-wait cycles. "
                "Combined, these measures project a 47% per-session emission reduction: 0.31 kg CO2e."
            ),
            "lifestyle_optimizations": (
                "Hotspot Ranking: (1) Workspace AC 7.38 kg [47.3%] (2) Gasoline Sedan 4.62 kg [29.6%] "
                "(3) Chicken Biryani 2.10 kg [13.5%]. "
                "Recommendation #1 — AC SETPOINT: Raise 21°C → 24°C (BEE India standard). Each °C = "
                "~6% load reduction; 3°C gain = 18% = −1.33 kg CO2e. Add 2 h pre-cool + economy schedule "
                "for further −0.80 kg CO2e. Total AC intervention: −2.13 kg CO2e. "
                "Recommendation #2 — COMMUTE: Carpool with one colleague (split emissions): −2.31 kg/day. "
                "Two WFH days/week: −9.24 kg/week (40% commute reduction). "
                "Recommendation #3 — DIET: Substitute chicken biryani with plant-based biryani (mushroom/paneer) "
                "3×/week: −4.95 kg CO2e/week. Tonight's plant-based dinner was optimal — maintain streak."
            ),
            "ledger_state": (
                "LEDGER REPORT — June 11, 2026 | "
                "Yesterday (June 10): 18.50 kg CO2e → Deficit: −3.50 kg. "
                "Today adjusted ceiling: 11.50 kg (15.0 − 3.50 carryover). "
                "Today actual: 15.61 kg. Overshoot vs adjusted ceiling: +4.11 kg. "
                "Cumulative 2-day deficit: −4.11 kg CO2e (avg 17.06 kg/day vs 15.0 target). "
                "Tomorrow's mandatory ceiling: 10.89 kg CO2e [= 45.0 − 34.11]. "
                "Gamified Rank: 🔴 Carbon Debtor L2 — Day 2 consecutive deficit. "
                "Risk: 3rd consecutive deficit triggers CRITICAL cascade status."
            ),
        },
        "deployment_directive": (
            "Raise AC setpoint to 24 °C immediately and plan WFH for June 12 to stay within "
            "the 10.89 kg rebalancing ceiling and prevent a 3-day CRITICAL cascade."
        ),
    }


# ── Gemini API call ───────────────────────────────────────────────────────────
def call_gemini(user_text: str, ledger: str, api_key: str) -> dict:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
        system_instruction=MASTER_PROMPT,
    )
    payload = f"[HISTORICAL LEDGER BASELINE]\n{ledger}\n\n--- USER ACTIVITIES & LOGS ---\n{user_text}"
    response = model.generate_content(payload)
    return extract_json(response.text)


def run_orchestrator(user_text: str, ledger: str, api_key: str = "") -> dict:
    if api_key and GENAI_AVAILABLE:
        try:
            return call_gemini(user_text, ledger, api_key)
        except Exception as exc:
            st.toast(f"⚠️ Gemini error: {exc} — falling back to demo mode", icon="⚠️")
    return mock_response(user_text)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════
_defaults = {
    "ledger_state": "Status: Neutral. Daily Allowance: 15.0 kg CO2e. No prior history loaded.",
    "messages":     [],
    "total_today":  0.0,
    "system_status": "OPTIMAL",
    "log_count":    0,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
api_key = ""  # scoped globally for the main section below

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🌱</div>
        <div class="sidebar-logo-name">EcoNode</div>
        <div class="sidebar-logo-sub">Carbon Intelligence · v2.0</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── API Configuration ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">🔑 API Configuration</div>', unsafe_allow_html=True)
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="AIzaSy...",
        help="Get your free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)",
        label_visibility="collapsed",
    )
    if api_key:
        if GENAI_AVAILABLE:
            st.success("✅ API key active — Live mode")
        else:
            st.warning("⚠️ `google-generativeai` not installed. Run: `pip install google-generativeai`")
    else:
        st.info("ℹ️ No API key — Demo mode active")

    st.divider()

    # ── Daily Budget Tracker ──────────────────────────────────────────────
    st.markdown('<div class="section-label">📊 Daily Budget</div>', unsafe_allow_html=True)
    st.markdown(budget_bar_html(st.session_state.total_today, 15.0), unsafe_allow_html=True)

    # ── Carbon Rank ───────────────────────────────────────────────────────
    rank = RANK_CFG[st.session_state.system_status]
    st.markdown(f"""
    <div style="text-align:center;padding:0.3rem 0 0.6rem;">
        <div style="font-size:0.62rem;color:#334155;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.4rem;">Current Rank</div>
        <div class="rank-badge" style="background:{rank['bg']};border:1px solid {rank['border']};color:{rank['fg']};">{rank['label']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Session Stats ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📈 Session Stats</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Logs Filed", st.session_state.log_count)
    c2.metric("CO₂e Today", f"{st.session_state.total_today:.1f} kg")

    st.divider()

    # ── Quick Tips ────────────────────────────────────────────────────────
    with st.expander("💡 What can I log?", expanded=False):
        st.markdown("""
        **🚗 Transit** — car type, km, flights  
        **🍽️ Diet** — meals, portion types  
        **⚡ Energy** — AC hours, kWh usage  
        **💻 Compute** — GPU/CPU jobs, runtimes  
        **📊 Ledger** — yesterday's total for deficit tracking
        """)

    st.divider()

    if st.button("🔄 Reset Session", use_container_width=True):
        for k in ("messages", "log_count"):
            st.session_state[k] = [] if isinstance(st.session_state[k], list) else 0
        st.session_state.total_today  = 0.0
        st.session_state.ledger_state = "Status: Neutral. Daily Allowance: 15.0 kg CO2e."
        st.session_state.system_status = "OPTIMAL"
        st.rerun()

    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0;color:#1e293b;font-size:0.62rem;line-height:1.6;">
        Powered by Gemini 1.5 Pro<br>
        Multi-Agent Carbon Protocol v2<br>
        © 2026 EcoNode Intelligence
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA — HEADER
# ══════════════════════════════════════════════════════════════════════════════
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.1rem;">
        <span style="font-size:2rem;">🌱</span>
        <div>
            <h1 class="eco-page-title">EcoNode Intelligence Engine</h1>
            <p class="eco-page-subtitle">Compute · Lifestyle · Ledger Protocols Active</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_status:
    status_now = st.session_state.system_status
    scfg = STATUS_CFG[status_now]
    st.markdown(f"""
    <div style="display:flex;justify-content:flex-end;align-items:center;height:100%;padding-top:0.4rem;">
        <span class="eco-status-pill {scfg['cls']}">{scfg['icon']} {status_now}</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ══════════════════════════════════════════════════════════════════════════════
# CHAT INPUT & MAIN EXECUTION LOOP
# ══════════════════════════════════════════════════════════════════════════════
if prompt := st.chat_input("Log your travel, meals, energy use, or compute workloads…"):

    # 1. Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Run orchestrator + render dashboard
    with st.chat_message("assistant"):
        with st.spinner("⚡ Routing to COMPUTE · LIFESTYLE · LEDGER protocols…"):
            data = run_orchestrator(prompt, st.session_state.ledger_state, api_key)

        status     = data.get("system_status", "WARNING")
        scfg       = STATUS_CFG.get(status, STATUS_CFG["WARNING"])
        ts         = data.get("execution_timestamp", "")
        total_kg   = data["ingestion_metrics"]["total_co2e_kg"]
        workloads  = data["ingestion_metrics"]["workloads_detected"]
        breakdown  = data.get("emission_breakdown", {})
        agents     = data["agent_outputs"]
        directive  = data.get("deployment_directive", "")

        # ── Status bar ──────────────────────────────────────────────────
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.7rem;flex-wrap:wrap;">
            <span class="eco-status-pill {scfg['cls']}">{scfg['icon']} {status}</span>
            <span class="ts-mono">{ts}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Deployment Directive ─────────────────────────────────────────
        st.markdown(f"""
        <div class="eco-directive">
            <strong>🎯 Deployment Directive</strong>
            {directive}
        </div>
        """, unsafe_allow_html=True)

        # ── Metrics row ──────────────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            "🌍 Session Impact",
            f"{total_kg:.2f} kg",
            delta=f"{total_kg - 15.0:+.2f} vs budget",
            delta_color="inverse",
        )
        m2.metric("📋 Workloads", len(workloads))
        top_src = max(breakdown, key=breakdown.get) if breakdown else "N/A"
        m3.metric("🔥 Top Source", top_src.split("(")[0].strip(), f"{breakdown.get(top_src, 0):.2f} kg")
        m4.metric("📅 Daily Ceiling", "15.0 kg CO2e")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Chart + Workloads (side by side) ────────────────────────────
        chart_col, list_col = st.columns([1.3, 1])

        with chart_col:
            st.markdown('<div class="section-label">📊 Emission Breakdown</div>', unsafe_allow_html=True)
            if breakdown and PLOTLY_AVAILABLE:
                render_donut_chart(breakdown)
            elif breakdown:
                max_v = max(breakdown.values())
                for src, val in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
                    pct = val / max_v
                    st.progress(pct, text=f"{src}: {val:.2f} kg")
            else:
                st.caption("No breakdown data returned.")

        with list_col:
            st.markdown('<div class="section-label">📋 Detected Workloads</div>', unsafe_allow_html=True)
            for w in workloads:
                st.markdown(f'<div class="workload-tag"><span style="color:#10b981;margin-top:1px;">▸</span><span>{w}</span></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Agent Insights (tabbed) ──────────────────────────────────────
        st.markdown('<div class="section-label">🤖 Agent Intelligence Reports</div>', unsafe_allow_html=True)

        tab_c, tab_l, tab_lg = st.tabs(["💻 Compute Agent", "🏃 Lifestyle Agent", "📊 Ledger Agent"])

        with tab_c:
            txt = agents.get("compute_optimizations", "None")
            if txt and txt.strip().lower() != "none":
                st.markdown(f"""
                <div class="agent-card">
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
                <div class="agent-card">
                    <div class="agent-card-label">🌿 [LIFESTYLE_PROTOCOL] — Behavioral Analysis</div>
                    <div class="agent-card-body">{txt}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No lifestyle data detected in this log entry.")

        with tab_lg:
            txt = agents.get("ledger_state", "")
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-card-label">📒 [LEDGER_PROTOCOL] — Rolling Budget State</div>
                <div class="agent-card-body">{txt}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Raw JSON for evaluators ──────────────────────────────────────
        with st.expander("🛠️ Raw JSON Payload — API / Evaluator View"):
            st.json(data)

        # ── Update session state ─────────────────────────────────────────
        st.session_state.ledger_state  = agents["ledger_state"]
        st.session_state.total_today  += total_kg
        st.session_state.system_status = status
        st.session_state.log_count    += 1

    # Save condensed message to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"**🎯 Directive:** {directive}  \n"
            f"**Status:** `{status}` &nbsp;·&nbsp; **Impact:** `{total_kg:.2f} kg CO2e`"
        ),
    })
