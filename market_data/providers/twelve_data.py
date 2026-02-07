"""
Twelve Data Market Data Provider
Implements market data ingestion via Twelve Data API
"""
from typing import Optional, Iterator
import requests
import time
from datetime import datetime
from .base import BaseMarketDataProvider, MarketEvent


class TwelveDataProvider(BaseMarketDataProvider):
    """
    Twelve Data real-time market data provider
    
    API Documentation: https://twelvedata.com/docs
    """
    
    BASE_URL = "https://api.twelvedata.com"
    
    def _validate_config(self, **kwargs) -> None:
        """Validate Twelve Data API key"""
        self.api_key = kwargs.get("api_key", "")
        if not self.api_key:
            raise ValueError("Twelve Data API key is required")
        
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # Free tier: 8 requests per minute
    
    def connect(self) -> bool:
        """Test API connectivity"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/time_series",
                params={
                    "symbol": self.instrument_id,
                    "interval": "1min",
                    "outputsize": 1,
                    "apikey": self.api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "status" not in data or data["status"] != "error":
                    self.is_connected = True
                    return True
            
            print(f"Twelve Data connection failed: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"Twelve Data connection error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close session"""
        self.session.close()
        self.is_connected = False
    
    def _respect_rate_limit(self) -> None:
        """Ensure rate limiting compliance"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def get_latest_price(self) -> Optional[MarketEvent]:
        """
        Fetch latest price from Twelve Data
        """
        try:
            self._respect_rate_limit()
            
            # Get real-time price quote
            response = self.session.get(
                f"{self.BASE_URL}/price",
                params={
                    "symbol": self.instrument_id,
                    "apikey": self.api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "price" in data:
                    price = float(data["price"])
                    
                    # Twelve Data doesn't always provide timestamp in price endpoint
                    # Use current time as fallback
                    timestamp_iso = datetime.now().isoformat()
                    
                    return MarketEvent(
                        timestamp=timestamp_iso,
                        instrument_id=self.instrument_id,
                        price=price
                    )
            
            return None
            
        except Exception as e:
            print(f"Twelve Data fetch error: {e}")
            return None
    
    def stream_prices(self) -> Iterator[MarketEvent]:
        """
        Stream prices by polling at regular intervals
        Note: Twelve Data offers WebSocket for paid plans
        """
        while self.is_connected:
            event = self.get_latest_price()
            if event:
                yield event
            time.sleep(10)  # Poll every 10 seconds to respect free tier limits
