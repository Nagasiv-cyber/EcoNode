"""EcoNode configuration constants, TypedDicts, and master prompt."""

__version__ = "2.1.0"

from typing import TypedDict, List, Dict

# Magic number replacements
DAILY_CEILING_KG: float = 15.0
MAX_INPUT_LENGTH: int = 2000
MAX_API_CALLS_PER_SESSION: int = 10
PEAK_GRID_MULTIPLIER: float = 1.18
OFF_PEAK_GRID_MULTIPLIER: float = 0.76
PETROL_SEDAN_KG_PER_KM: float = 0.170
ELECTRIC_AUTO_KG_PER_KM: float = 0.045
GPU_KG_PER_HOUR: float = 0.095
INDIA_GRID_KG_PER_KWH: float = 0.820
WEEKLY_CEILING_KG: float = 105.0

class IngestionMetrics(TypedDict):
    """Type definition for ingestion metrics."""
    workloads_detected: List[str]
    total_co2e_kg: float

class AgentOutputs(TypedDict):
    """Type definition for agent outputs."""
    compute_optimizations: str
    lifestyle_optimizations: str
    ledger_state: str

class ApiResponse(TypedDict):
    """Type definition for the Gemini API response."""
    execution_timestamp: str
    system_status: str
    ingestion_metrics: IngestionMetrics
    emission_breakdown: Dict[str, float]
    agent_outputs: AgentOutputs
    deployment_directive: str

STATUS_CFG: Dict[str, Dict[str, str]] = {
    "OPTIMAL": {"icon": "🟢", "cls": "eco-optimal", "color": "#10b981"},
    "WARNING":  {"icon": "🟡", "cls": "eco-warning",  "color": "#f59e0b"},
    "CRITICAL": {"icon": "🔴", "cls": "eco-critical",  "color": "#ef4444"},
}

RANK_CFG: Dict[str, Dict[str, str]] = {
    "OPTIMAL": {"label": "🌿 Carbon Neutral",   "bg": "#052e16", "fg": "#34d399", "border": "#10b981"},
    "WARNING":  {"label": "⚠️ Carbon Debtor L1", "bg": "#451a03", "fg": "#fbbf24", "border": "#f59e0b"},
    "CRITICAL": {"label": "🔴 Carbon Debtor L2", "bg": "#450a0a", "fg": "#f87171", "border": "#ef4444"},
}

CHART_COLORS: List[str] = [
    "#10b981", "#34d399", "#f59e0b", "#ef4444",
    "#8b5cf6", "#06b6d4", "#ec4899", "#f97316",
    "#a3e635", "#fb923c",
]

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
