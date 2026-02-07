"""
Risk Event Detection
Detects meaningful changes in Greeks and risk metrics
"""
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

from config.settings import config


@dataclass
class RiskEvent:
    """Represents a detected risk event"""
    timestamp: str
    event_type: str  # e.g., "DELTA_SPIKE", "REGIME_CHANGE", "GAMMA_SURGE"
    severity: str  # "LOW", "MEDIUM", "HIGH"
    description: str
    old_value: float
    new_value: float
    change_pct: float
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_pct": self.change_pct
        }


class RiskEventDetector:
    """
    Stateful risk event detector
    
    Tracks previous risk metrics and detects significant changes
    """
    
    def __init__(self):
        self.previous_metrics: Optional[Dict] = None
        self.event_history: List[RiskEvent] = []
        self.max_history_size = 100
    
    def detect_events(self, current_metrics: Dict) -> List[RiskEvent]:
        """
        Detect risk events by comparing current to previous metrics
        
        Args:
            current_metrics: Current risk metrics
        
        Returns:
            List of detected risk events
        """
        events = []
        
        if self.previous_metrics is None:
            # First data point, no events
            self.previous_metrics = current_metrics
            return events
        
        timestamp = current_metrics.get("timestamp", datetime.now().isoformat())
        thresholds = config.risk_thresholds
        
        # Check Delta change
        old_delta = self.previous_metrics.get("delta", 0.0)
        new_delta = current_metrics.get("delta", 0.0)
        if self._significant_change(old_delta, new_delta, thresholds.delta_change_threshold):
            events.append(RiskEvent(
                timestamp=timestamp,
                event_type="DELTA_CHANGE",
                severity=self._classify_severity(old_delta, new_delta, thresholds.delta_change_threshold),
                description=f"Delta changed from {old_delta:.4f} to {new_delta:.4f}",
                old_value=old_delta,
                new_value=new_delta,
                change_pct=self._calc_change_pct(old_delta, new_delta)
            ))
        
        # Check Gamma change
        old_gamma = self.previous_metrics.get("gamma", 0.0)
        new_gamma = current_metrics.get("gamma", 0.0)
        if self._significant_change(old_gamma, new_gamma, thresholds.gamma_change_threshold):
            events.append(RiskEvent(
                timestamp=timestamp,
                event_type="GAMMA_CHANGE",
                severity=self._classify_severity(old_gamma, new_gamma, thresholds.gamma_change_threshold),
                description=f"Gamma changed from {old_gamma:.6f} to {new_gamma:.6f}",
                old_value=old_gamma,
                new_value=new_gamma,
                change_pct=self._calc_change_pct(old_gamma, new_gamma)
            ))
        
        # Check Theta change
        old_theta = self.previous_metrics.get("theta", 0.0)
        new_theta = current_metrics.get("theta", 0.0)
        if self._significant_change(old_theta, new_theta, thresholds.theta_change_threshold):
            events.append(RiskEvent(
                timestamp=timestamp,
                event_type="THETA_CHANGE",
                severity=self._classify_severity(old_theta, new_theta, thresholds.theta_change_threshold),
                description=f"Theta changed from {old_theta:.4f} to {new_theta:.4f}",
                old_value=old_theta,
                new_value=new_theta,
                change_pct=self._calc_change_pct(old_theta, new_theta)
            ))
        
        # Check Vega change
        old_vega = self.previous_metrics.get("vega", 0.0)
        new_vega = current_metrics.get("vega", 0.0)
        if self._significant_change(old_vega, new_vega, thresholds.vega_change_threshold):
            events.append(RiskEvent(
                timestamp=timestamp,
                event_type="VEGA_CHANGE",
                severity=self._classify_severity(old_vega, new_vega, thresholds.vega_change_threshold),
                description=f"Vega changed from {old_vega:.4f} to {new_vega:.4f}",
                old_value=old_vega,
                new_value=new_vega,
                change_pct=self._calc_change_pct(old_vega, new_vega)
            ))
        
        # Check Risk Regime change
        old_regime = self.previous_metrics.get("risk_regime", "UNKNOWN")
        new_regime = current_metrics.get("risk_regime", "UNKNOWN")
        if old_regime != new_regime:
            events.append(RiskEvent(
                timestamp=timestamp,
                event_type="REGIME_CHANGE",
                severity=self._regime_change_severity(old_regime, new_regime),
                description=f"Risk regime transitioned from {old_regime} to {new_regime}",
                old_value=0.0,
                new_value=0.0,
                change_pct=0.0
            ))
        
        # Update previous metrics
        self.previous_metrics = current_metrics
        
        # Add to history
        self.event_history.extend(events)
        
        # Trim history
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        return events
    
    def _significant_change(self, old_value: float, new_value: float, threshold: float) -> bool:
        """Check if change exceeds threshold"""
        if abs(old_value) < 1e-10:  # Avoid division by zero
            return abs(new_value) > threshold
        
        change_pct = abs((new_value - old_value) / old_value)
        return change_pct >= threshold
    
    def _calc_change_pct(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change"""
        if abs(old_value) < 1e-10:
            return 0.0 if abs(new_value) < 1e-10 else 100.0
        
        return ((new_value - old_value) / old_value) * 100.0
    
    def _classify_severity(self, old_value: float, new_value: float, threshold: float) -> str:
        """Classify event severity"""
        if abs(old_value) < 1e-10:
            return "MEDIUM"
        
        change_pct = abs((new_value - old_value) / old_value)
        
        if change_pct >= threshold * 3:
            return "HIGH"
        elif change_pct >= threshold * 1.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _regime_change_severity(self, old_regime: str, new_regime: str) -> str:
        """Determine severity of regime change"""
        regime_order = {"STABLE": 0, "SENSITIVE": 1, "FRAGILE": 2}
        
        old_level = regime_order.get(old_regime, 1)
        new_level = regime_order.get(new_regime, 1)
        
        diff = abs(new_level - old_level)
        
        if diff >= 2:
            return "HIGH"
        elif diff == 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_recent_events(self, count: int = 10) -> List[RiskEvent]:
        """Get most recent events"""
        return self.event_history[-count:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self.event_history.clear()


# Global detector instance
risk_event_detector = RiskEventDetector()
