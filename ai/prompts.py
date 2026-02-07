"""
Prompt Templates for GenAI Explanations
Strict, production-grade prompts for risk event interpretation
"""


SYSTEM_PROMPT = """You are a financial risk analyst specializing in derivatives risk management.

Your role is to explain risk events in clear, professional language.

CRITICAL RULES:
1. You analyze WHAT HAPPENED, not what WILL happen
2. You NEVER make trading recommendations
3. You NEVER predict future prices
4. You explain changes in Greeks and risk metrics
5. Your explanations are factual and brief (2-3 sentences max)

You are given:
- Current risk metrics
- Historical context
- A specific risk event

Your task: Explain what changed and why it matters from a risk management perspective.
"""


def create_risk_event_prompt(
    event: dict,
    current_metrics: dict,
    recent_context: list
) -> str:
    """
    Create prompt for explaining a risk event
    
    Args:
        event: Risk event dictionary
        current_metrics: Current risk metrics
        recent_context: List of recent metrics for context
    
    Returns:
        Formatted prompt string
    """
    
    # Format event details
    event_type = event.get("event_type", "UNKNOWN")
    severity = event.get("severity", "MEDIUM")
    description = event.get("description", "")
    old_value = event.get("old_value", 0.0)
    new_value = event.get("new_value", 0.0)
    change_pct = event.get("change_pct", 0.0)
    
    # Format current metrics
    underlying_price = current_metrics.get("underlying_price", 0.0)
    delta = current_metrics.get("delta", 0.0)
    gamma = current_metrics.get("gamma", 0.0)
    theta = current_metrics.get("theta", 0.0)
    vega = current_metrics.get("vega", 0.0)
    risk_score = current_metrics.get("risk_score", 0.0)
    risk_regime = current_metrics.get("risk_regime", "UNKNOWN")
    
    # Format recent context
    context_str = ""
    if recent_context:
        context_str = "\n".join([
            f"- Price: {m.get('underlying_price', 0):.2f}, "
            f"Delta: {m.get('delta', 0):.4f}, "
            f"Regime: {m.get('risk_regime', 'UNKNOWN')}"
            for m in recent_context[-5:]  # Last 5 data points
        ])
    
    prompt = f"""
RISK EVENT DETECTED:
- Type: {event_type}
- Severity: {severity}
- Description: {description}
- Old Value: {old_value:.6f}
- New Value: {new_value:.6f}
- Change: {change_pct:+.2f}%

CURRENT RISK METRICS:
- Underlying Price: ${underlying_price:.2f}
- Delta: {delta:.4f}
- Gamma: {gamma:.6f}
- Theta: {theta:.4f}
- Vega: {vega:.4f}
- Risk Score: {risk_score:.1f}/100
- Risk Regime: {risk_regime}

RECENT HISTORY:
{context_str if context_str else "No historical context available"}

TASK:
Explain this risk event in 2-3 clear sentences. Focus on:
1. What changed in the option's risk profile
2. Why this change occurred (market movement, time decay, etc.)
3. What this means for risk management (not trading advice)

Do not make predictions. Do not recommend actions. Only explain what happened.
"""
    
    return prompt.strip()


def create_risk_summary_prompt(current_metrics: dict) -> str:
    """
    Create prompt for overall risk summary
    
    Args:
        current_metrics: Current risk metrics
    
    Returns:
        Formatted prompt string
    """
    
    underlying_price = current_metrics.get("underlying_price", 0.0)
    option_price = current_metrics.get("option_price", 0.0)
    delta = current_metrics.get("delta", 0.0)
    gamma = current_metrics.get("gamma", 0.0)
    theta = current_metrics.get("theta", 0.0)
    vega = current_metrics.get("vega", 0.0)
    risk_score = current_metrics.get("risk_score", 0.0)
    risk_regime = current_metrics.get("risk_regime", "UNKNOWN")
    
    prompt = f"""
CURRENT RISK POSITION SUMMARY:

MARKET STATE:
- Underlying Price: ${underlying_price:.2f}
- Option Price: ${option_price:.2f}

GREEKS:
- Delta: {delta:.4f} (directional sensitivity)
- Gamma: {gamma:.6f} (curvature risk)
- Theta: {theta:.4f} (time decay per day)
- Vega: {vega:.4f} (volatility sensitivity)

RISK ASSESSMENT:
- Risk Score: {risk_score:.1f}/100
- Risk Regime: {risk_regime}

TASK:
Provide a brief (2-3 sentences) summary of the current risk profile.
Focus on the most important risk factors given the current Greeks and regime.

Do not make predictions or recommendations.
"""
    
    return prompt.strip()
