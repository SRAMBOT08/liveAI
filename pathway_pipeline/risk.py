"""
Risk Metrics and Scoring
Computes risk health score, regimes, and shock scenarios
"""
import numpy as np
from typing import Dict, Tuple
from datetime import datetime

from config.settings import config
from config.instruments import DEFAULT_OPTION
from .greeks import calculate_option_greeks, shock_greeks


def compute_risk_score(greeks: Dict) -> float:
    """
    Compute Risk Health Score (0-100)
    
    Lower score = more stable/healthy
    Higher score = more fragile/risky
    
    Factors:
    - High absolute delta: more directional risk
    - High gamma: more convexity risk (rapid delta changes)
    - High absolute theta: time decay risk
    - High vega: volatility sensitivity
    
    Args:
        greeks: Dictionary with delta, gamma, theta, vega
    
    Returns:
        Risk score between 0 and 100
    """
    
    delta = abs(greeks.get("delta", 0.0))
    gamma = abs(greeks.get("gamma", 0.0))
    theta = abs(greeks.get("theta", 0.0))
    vega = abs(greeks.get("vega", 0.0))
    
    # Weights for each component (tunable)
    w_delta = 0.25
    w_gamma = 0.35  # Gamma is critical for risk
    w_theta = 0.20
    w_vega = 0.20
    
    # Normalize components (these are heuristic scaling factors)
    delta_score = min(delta * 100, 100)  # Delta is 0-1, scale to 0-100
    gamma_score = min(gamma * 1000, 100)  # Gamma is typically small
    theta_score = min(theta * 10, 100)  # Theta is moderate
    vega_score = min(vega * 5, 100)  # Vega is moderate
    
    # Weighted sum
    risk_score = (
        w_delta * delta_score +
        w_gamma * gamma_score +
        w_theta * theta_score +
        w_vega * vega_score
    )
    
    # Clamp to 0-100
    return float(np.clip(risk_score, 0.0, 100.0))


def determine_risk_regime(risk_score: float) -> str:
    """
    Determine risk regime based on score
    
    Args:
        risk_score: Risk health score
    
    Returns:
        Risk regime: STABLE, SENSITIVE, or FRAGILE
    """
    thresholds = config.risk_thresholds
    
    if risk_score <= thresholds.stable_max:
        return "STABLE"
    elif risk_score <= thresholds.sensitive_max:
        return "SENSITIVE"
    else:
        return "FRAGILE"


def compute_shock_scenarios(
    base_price: float,
    current_time: datetime = None,
    volatility: float = 0.20
) -> Dict:
    """
    Compute Greeks for shock scenarios
    
    Args:
        base_price: Current futures price
        current_time: Current timestamp
        volatility: Implied volatility
    
    Returns:
        Dictionary with shocked Greeks for each scenario
    """
    
    scenarios = {}
    
    for shock_pct in config.risk_thresholds.shock_scenarios:
        shocked_greeks = shock_greeks(base_price, shock_pct, current_time, volatility)
        label = f"shock_{'+' if shock_pct >= 0 else ''}{int(shock_pct * 100)}pct"
        scenarios[label] = shocked_greeks
    
    return scenarios


def compute_full_risk_metrics(
    underlying_price: float,
    timestamp: str,
    instrument_id: str,
    volatility: float = 0.20
) -> Dict:
    """
    Compute comprehensive risk metrics
    
    Args:
        underlying_price: Current futures price
        timestamp: ISO timestamp
        instrument_id: Instrument identifier
        volatility: Implied volatility
    
    Returns:
        Complete risk metrics dictionary
    """
    
    # Parse timestamp
    try:
        current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except:
        current_time = datetime.now()
    
    # Calculate base Greeks
    greeks_data = calculate_option_greeks(underlying_price, current_time, volatility)
    
    # Compute risk score
    risk_score = compute_risk_score(greeks_data)
    
    # Determine regime
    risk_regime = determine_risk_regime(risk_score)
    
    # Compute shock scenarios
    shocks = compute_shock_scenarios(underlying_price, current_time, volatility)
    
    return {
        "timestamp": timestamp,
        "instrument_id": instrument_id,
        "underlying_price": underlying_price,
        "option_price": greeks_data["option_price"],
        "delta": greeks_data["delta"],
        "gamma": greeks_data["gamma"],
        "theta": greeks_data["theta"],
        "vega": greeks_data["vega"],
        "rho": greeks_data["rho"],
        "risk_score": risk_score,
        "risk_regime": risk_regime,
        "shock_up_1pct": shocks.get("shock_+1pct", {}).get("delta", 0.0),
        "shock_down_1pct": shocks.get("shock_-1pct", {}).get("delta", 0.0),
        "shock_up_5pct": shocks.get("shock_+5pct", {}).get("delta", 0.0),
        "shock_down_5pct": shocks.get("shock_-5pct", {}).get("delta", 0.0),
    }


def detect_significant_change(old_value: float, new_value: float, threshold: float) -> bool:
    """
    Detect if change exceeds threshold
    
    Args:
        old_value: Previous value
        new_value: Current value
        threshold: Threshold as decimal (e.g., 0.05 for 5%)
    
    Returns:
        True if change exceeds threshold
    """
    if old_value == 0:
        return new_value != 0
    
    change_pct = abs((new_value - old_value) / old_value)
    return change_pct >= threshold
