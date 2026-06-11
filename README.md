# 🌱 EcoNode: Multi-Agent Carbon Intelligence Engine

EcoNode is an advanced, context-aware Carbon Auditing and GreenOps optimization platform built for pure-software ecosystems. Moving away from traditional static carbon calculators, EcoNode utilizes a coordinated multi-agent orchestration architecture to parse text-based user logs, evaluate dense computational/machine-learning pipelines, maintain a persistent rolling emission ledger, and deliver structured, real-time optimization strategies.

## 🎯 Chosen Vertical

* **Platform Category:** Carbon Footprint Awareness Platform
* **Target Audience:** Modern developers, technical professionals, and carbon-conscious organizations.

---

## 🧠 Approach & Core Logic Architecture

EcoNode relies on a unified **Master Orchestrator Engine** that coordinates three specialized analytical sub-protocols to interpret real-world and digital context:

1. **🏃 Lifestyle Protocol (Semantic Auditor):** Parses unstructured daily logs (transit types, commute metrics, dietary footprints) and converts them into precise CO₂e values using integrated emissions tables.
2. **💻 Compute Protocol (GreenOps & ML Profiler):** Analyzes technical inputs — ranging from low-power microcontroller telemetry to continuous GPU-accelerated Machine Learning model training or algorithmic backtesting. It estimates algorithmic complexity and recommends power-aware time-shifting strategies.
3. **📊 Ledger Protocol (State Tracking Manager):** Implements a persistent, localized micro-economy. It maps daily emissions against a strict **15.0 kg CO₂e ceiling**, tracking credit surpluses or rolling deficits over a continuous session timeline.

---

## 🛠️ How the Solution Works (System Pipeline)

```
[User Text Input] ──> [Master Orchestrator] ──> [JSON Schema Enforcer]
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
  [Lifestyle Agent]    [Compute Agent]      [Ledger Agent]
  (Transit/Diet CO₂)  (GPU/Code Metrics)  (State Management)
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                  [Synthesis Layer Engine]
                              │
                              ▼
          [Premium Streamlit Glassmorphism UI]
```

1. **Data Ingestion:** The user submits lifestyle updates or workload descriptions via the Streamlit chat interface.
2. **Context Routing:** The system injects a comprehensive 4-Phase system instruction prompt alongside the session's active historical baseline, forcing a strict structured JSON payload response.
3. **Deficit Enforcement:** If the Ledger Agent flags a deficit from a prior cycle, the Master Orchestrator automatically restricts the target ceiling for the active session, adapting its behavioral recommendations to regain carbon neutrality.
4. **Visual Synthesis:** The backend handles string sanitisation via a 3-layer JSON fallback extractor. The parsed data is mapped to a dark-mode glassmorphism UI containing dynamic Plotly donut charts, 4-column metric sheets, tabbed agent insight panels, and expandable raw JSON blocks for deep technical auditing.

---

## 📋 Technical Assumptions & Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Daily CO₂e Ceiling | **15.0 kg** | Rolling per-user-cycle budget |
| India Grid Intensity | **0.820 kg CO₂e / kWh** | CEA National 2025 average |
| Peak Grid Multiplier | **×1.18** (13:00–19:00 IST) | Thermal-heavy afternoon demand |
| Off-Peak Grid Multiplier | **×0.76** (00:00–06:00 IST) | Renewable-heavy night floor |
| Gasoline Sedan | **0.210 kg CO₂e / km** | DEFRA Scope 1 road transport |
| RTX 4070 Laptop GPU | **0.115 kW** full-load TDP + 50% system overhead |
| AC (1.5-ton split) | **1.50 kW** rated draw |
| Chicken (per serving) | **1.38 kg CO₂e** (200g at 6.9 kg/kg) |

---

## 🚀 Installation & Running Locally

Ensure your terminal is navigated to the project workspace:

```bash
cd C:\Users\K.Visagan\Downloads\econode
```

### 1. Install System Dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch the Application

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

> **No API key?** No problem. If no Gemini API key is entered into the secure sidebar runtime field, EcoNode automatically switches into a fully-interactive **demo mode** using pre-compiled structural mock states — the complete UI dashboard, charts, and all three agent panels remain fully functional for evaluation at any time.

---

## 🔑 API Key Configuration (Live Mode)

1. Visit [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) and generate a free Gemini API key.
2. Paste it into the **🔑 API Configuration** field in the sidebar at runtime.
3. The app instantly switches from demo mode to **Live Gemini 1.5 Pro** inference with `response_mime_type="application/json"` enforced.

No `.env` file is required — the key is held only in the active Streamlit session.

---

## 📁 Project Structure

```
econode/
├── app.py              # Main Streamlit application (UI + backend + orchestrator)
├── requirements.txt    # Python dependencies
├── .env.example        # API key template (rename to .env if preferred)
├── .gitignore          # Excludes secrets and cache from version control
└── README.md           # This file
```

---

## ✅ Final Submission Checklist

- [ ] `.env` (if populated) is listed in `.gitignore` — no tokens pushed to the repository
- [ ] `app.py`, `requirements.txt`, and `README.md` committed to the primary branch
- [ ] App runs cleanly in demo mode (no API key required for judges to evaluate)
- [ ] Raw JSON expander visible in the UI for evaluator transparency

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit + Vanilla CSS (glassmorphism, dark mode) |
| Charts | Plotly (interactive donut chart with pull-out highlight) |
| AI Backend | Google Gemini 1.5 Pro via `google-generativeai` SDK |
| JSON Enforcement | `response_mime_type="application/json"` + 3-layer regex fallback |
| State Management | Streamlit Session State (rolling ledger, chat history) |
| Typography | Inter (UI) + JetBrains Mono (timestamps / code) via Google Fonts |

---

*Built with ❤️ for the hackathon. EcoNode — Because every kilogram counts.*
