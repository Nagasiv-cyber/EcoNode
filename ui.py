"""EcoNode Streamlit UI rendering functions with full ARIA accessibility support."""

__version__ = "2.1.0"

from typing import Dict, List

import pandas as pd
import streamlit as st
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from config import CHART_COLORS

@st.cache_data
def get_css() -> str:
    """Return the cached CSS styling block.

    Returns:
        HTML string containing CSS styles.
    """
    return """
    <!-- Content Security Policy: Google Fonts -->
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #020617;
        color: #f8fafc;
    }

    /* Ensure visible focus indicators for accessibility */
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

def budget_bar_html(used: float, ceiling: float = 15.0) -> str:
    """Generate the HTML string for the real-time budget progress bar.

    Args:
        used: The amount of CO2e used.
        ceiling: The maximum allowed CO2e.

    Returns:
        HTML string.
    """
    pct = used / max(ceiling, 0.01) * 100
    fill_pct = min(pct, 100)
    color = "#10b981" if pct <= 70 else "#f59e0b" if pct <= 100 else "#ef4444"
    return f"""
    <div style="margin:0.2rem 0 0.5rem;" role="progressbar" aria-valuenow="{used}" aria-valuemin="0" aria-valuemax="{ceiling}" aria-label="Daily carbon budget: {used:.2f} kg of {ceiling:.1f} kg used">
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
        breakdown: Dictionary mapping source strings to float values.
    """
    if not PLOTLY_AVAILABLE or not breakdown:
        st.caption("Chart disabled or no data available.")
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
            font=dict(family="Inter", size=9, color="#94a3b8"),
            bgcolor="rgba(0,0,0,0)",
            orientation="v",
            x=1.02,
            y=0.5,
            itemsizing="constant",
        ),
        annotations=[dict(
            text=f"<b style='font-size:15px;color:#e2e8f0'>{total:.2f}</b><br><span style='color:#94a3b8'>kg CO₂e</span>",
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
