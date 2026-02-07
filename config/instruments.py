"""
Financial Instrument Definitions
Defines futures contracts and options for risk computation
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal


@dataclass
class FuturesContract:
    """
    Futures contract specification (CME-style)
    """
    symbol: str  # e.g., "GC"
    name: str  # e.g., "Gold Futures"
    exchange: str  # e.g., "COMEX"
    contract_size: float  # e.g., 100 oz for gold
    tick_size: float  # minimum price movement
    currency: str  # e.g., "USD"
    
    # For demo purposes
    current_price: float  # starting/reference price
    

@dataclass
class OptionContract:
    """
    Option contract specification
    """
    symbol: str  # e.g., "GC_C_2100"
    underlying: str  # futures symbol, e.g., "GC"
    option_type: Literal["call", "put"]
    strike: float
    expiration: datetime
    
    # Black-76 parameters
    risk_free_rate: float  # annualized, e.g., 0.05 for 5%
    
    def time_to_expiration_years(self, current_time: datetime = None) -> float:
        """Calculate time to expiration in years"""
        if current_time is None:
            current_time = datetime.now()
        
        days_remaining = (self.expiration - current_time).days
        return max(days_remaining / 365.0, 0.0001)  # avoid division by zero


# ============================================================================
# DEFAULT INSTRUMENTS FOR DEMO
# ============================================================================

# Gold Futures Contract
GOLD_FUTURES = FuturesContract(
    symbol="GC",
    name="Gold Futures",
    exchange="COMEX",
    contract_size=100.0,  # 100 troy ounces
    tick_size=0.10,
    currency="USD",
    current_price=2050.0  # starting price for demo
)

# Gold Call Option
GOLD_CALL_OPTION = OptionContract(
    symbol="GC_C_2100",
    underlying="GC",
    option_type="call",
    strike=2100.0,
    expiration=datetime.now() + timedelta(days=90),  # 3 months out
    risk_free_rate=0.045  # 4.5% annual risk-free rate
)

# Gold Put Option (alternative)
GOLD_PUT_OPTION = OptionContract(
    symbol="GC_P_2000",
    underlying="GC",
    option_type="put",
    strike=2000.0,
    expiration=datetime.now() + timedelta(days=90),
    risk_free_rate=0.045
)


# Default selection for the system
DEFAULT_FUTURES = GOLD_FUTURES
DEFAULT_OPTION = GOLD_CALL_OPTION


def get_instrument_info() -> dict:
    """
    Returns instrument information for display/logging
    """
    return {
        "futures": {
            "symbol": DEFAULT_FUTURES.symbol,
            "name": DEFAULT_FUTURES.name,
            "current_price": DEFAULT_FUTURES.current_price,
            "contract_size": DEFAULT_FUTURES.contract_size
        },
        "option": {
            "symbol": DEFAULT_OPTION.symbol,
            "type": DEFAULT_OPTION.option_type,
            "strike": DEFAULT_OPTION.strike,
            "expiration": DEFAULT_OPTION.expiration.isoformat(),
            "tte_days": (DEFAULT_OPTION.expiration - datetime.now()).days
        }
    }
