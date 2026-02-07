"""
Base Market Data Provider Interface
All market data providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Iterator
from datetime import datetime
from dataclasses import dataclass
import json


@dataclass
class MarketEvent:
    """
    Unified market event schema
    All providers must output this exact format
    """
    timestamp: str  # ISO-8601 format
    instrument_id: str  # e.g., "GC" for Gold futures
    price: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Kafka serialization"""
        return {
            "timestamp": self.timestamp,
            "instrument_id": self.instrument_id,
            "price": self.price
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MarketEvent':
        """Create from dictionary"""
        return cls(
            timestamp=data["timestamp"],
            instrument_id=data["instrument_id"],
            price=data["price"]
        )


class BaseMarketDataProvider(ABC):
    """
    Abstract base class for all market data providers
    
    Design principles:
    1. All providers output MarketEvent objects
    2. Providers handle their own authentication
    3. Providers handle their own error recovery
    4. Providers are stateless (no business logic)
    """
    
    def __init__(self, instrument_id: str, **kwargs):
        """
        Initialize provider
        
        Args:
            instrument_id: The instrument to track (e.g., "GC")
            **kwargs: Provider-specific configuration
        """
        self.instrument_id = instrument_id
        self.is_connected = False
        self._validate_config(**kwargs)
    
    @abstractmethod
    def _validate_config(self, **kwargs) -> None:
        """
        Validate provider-specific configuration
        Raise ValueError if configuration is invalid
        """
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to data source
        Returns True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to data source
        """
        pass
    
    @abstractmethod
    def get_latest_price(self) -> Optional[MarketEvent]:
        """
        Fetch the latest market price
        Returns MarketEvent or None if unavailable
        """
        pass
    
    @abstractmethod
    def stream_prices(self) -> Iterator[MarketEvent]:
        """
        Stream market prices continuously
        Yields MarketEvent objects
        """
        pass
    
    def health_check(self) -> bool:
        """
        Check if provider is operational
        """
        try:
            event = self.get_latest_price()
            return event is not None and self.is_connected
        except Exception:
            return False
    
    def get_provider_info(self) -> Dict:
        """
        Return provider metadata
        """
        return {
            "provider": self.__class__.__name__,
            "instrument": self.instrument_id,
            "connected": self.is_connected
        }
