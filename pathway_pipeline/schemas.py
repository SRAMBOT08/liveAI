"""
Pathway Schemas
Defines data schemas for Pathway streaming tables
"""
import pathway as pw


class MarketEventSchema(pw.Schema):
    """Schema for incoming market events from Kafka"""
    timestamp: str
    instrument_id: str
    price: float


class PriceStateSchema(pw.Schema):
    """Schema for price state tracking"""
    timestamp: str
    instrument_id: str
    price: float
    price_previous: float
    price_change: float
    price_change_pct: float


class GreeksSchema(pw.Schema):
    """Schema for computed Greeks"""
    timestamp: str
    instrument_id: str
    underlying_price: float
    option_price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class RiskMetricsSchema(pw.Schema):
    """Schema for risk metrics"""
    timestamp: str
    instrument_id: str
    risk_score: float
    risk_regime: str
    delta: float
    gamma: float
    theta: float
    vega: float
    shock_up_1pct: float
    shock_down_1pct: float
    shock_up_5pct: float
    shock_down_5pct: float


class RiskEventSchema(pw.Schema):
    """Schema for detected risk events"""
    timestamp: str
    event_type: str
    severity: str
    description: str
    old_value: float
    new_value: float
    change_pct: float
