# 🌱 EcoNode: Multi-Agent Carbon Intelligence Engine

![CI](https://github.com/Nagasiv-cyber/EcoNode/actions/workflows/test.yml/badge.svg)

EcoNode is a hyper-optimized Core Inference Engine designed to process multi-modal user activity logs and execute deterministic Carbon Auditing, GreenOps compute calculation, and Ledger state balancing. Built natively for Streamlit, the platform orchestrates LLMs using the google-genai SDK to translate free-text natural inputs into actionable behavioral corrections and compute load time-shifting protocols.

## Project Structure
```text
econode/
├── app.py                          # Main Streamlit entry point
├── config.py                       # Constants, TypedDicts, Master Prompt
├── utils.py                        # JSON extraction, validation, UI helpers
├── agents.py                       # Gemini API, mock responses, orchestrator
├── ui.py                           # ARIA-accessible rendering functions
├── requirements.txt                # Pinned dependencies
├── pyproject.toml                  # Pytest + coverage + ruff config
├── .env.example                    # API key template
├── .gitignore                      # Excludes secrets and cache
├── README.md                       # This file
└── tests/
    └── test_econode.py             # 30+ unit tests, 90%+ coverage
└── .github/
    └── workflows/
        └── test.yml                # CI: lint + security scan + pytest
```

## Features
- **Deterministic Emission Modeling**: Grounded against specific kg CO2e baselines (Grid emissions, EV transit, dietary choices, compute profiling).
- **Gamified Ledger System**: A rolling carbon budget system that penalizes deficits and dynamically adjusts daily emission ceilings.
- **GreenOps Directives**: Active hardware workload profiling (e.g., RTX 4070 inferences) integrated with off-peak grid heuristics to recommend optimal processing windows.
- **Accessible Dashboards**: High-contrast, ARIA-labeled visualizations powered by Plotly for WCAG compliance.
- **Robust Multi-Agent Framework**: Separate analytical scopes for compute optimizations, lifestyle shifts, and ledger maintenance tracking.

## Installation and Execution
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Gemini key to `.env` or paste it directly in the sidebar GUI.
4. Run locally: `streamlit run app.py`

## Final Submission Checklist
- [x] Modular architecture (config, utils, agents, ui, app)
- [x] 30+ unit tests with 90%+ coverage
- [x] GitHub Actions CI passing (lint + bandit + pytest)
- [x] Full ARIA accessibility (role, aria-label, aria-live)
- [x] Input sanitization and rate limiting
- [x] google-genai SDK (latest, non-deprecated)
- [x] Demo mode banner visible without API key
