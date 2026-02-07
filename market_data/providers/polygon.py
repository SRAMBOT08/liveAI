"""
Polygon.io Market Data Provider
Implements CME futures data ingestion via Polygon.io API
"""
from typing import Optional, Iterator
import requests
import time
from datetime import datetime
from .base import BaseMarketDataProvider, MarketEvent


class PolygonProvider(BaseMarketDataProvider):
    """
    Polygon.io real-time and historical market data provider
    
    API Documentation: https://polygon.io/docs/options/getting-started
    """
    
    BASE_URL = "https://api.polygon.io"
    
    def _validate_config(self, **kwargs) -> None:
        """Validate Polygon API key"""
        self.api_key = kwargs.get("api_key", "")
        if not self.api_key:
            raise ValueError("Polygon API key is required")
        
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 10 requests per second for paid tier
    
    def connect(self) -> bool:
        """Test API connectivity"""
        try:
            # Test with a simple status check
            response = self.session.get(
                f"{self.BASE_URL}/v2/aggs/ticker/{self.instrument_id}/prev",
                params={"apiKey": self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                self.is_connected = True
                return True
            else:
                print(f"Polygon connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Polygon connection error: {e}")
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
        Fetch latest price from Polygon
        Uses previous day's close or real-time trade
        """
        try:
            self._respect_rate_limit()
            
            # Get last trade
            response = self.session.get(
                f"{self.BASE_URL}/v2/last/trade/{self.instrument_id}",
                params={"apiKey": self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "results" in data:
                    result = data["results"]
                    price = result.get("p", 0.0)  # 'p' is price
                    timestamp_ns = result.get("t", 0)  # 't' is timestamp in nanoseconds
                    
                    # Convert timestamp to ISO-8601
                    dt = datetime.fromtimestamp(timestamp_ns / 1e9)
                    timestamp_iso = dt.isoformat()
                    
                    return MarketEvent(
                        timestamp=timestamp_iso,
                        instrument_id=self.instrument_id,
                        price=float(price)
                    )
            
            return None
            
        except Exception as e:
            print(f"Polygon fetch error: {e}")
            return None
    
    def stream_prices(self) -> Iterator[MarketEvent]:
        """
        Stream prices by polling at regular intervals
        Polygon.io WebSocket would be used in true production
        """
        while self.is_connected:
            event = self.get_latest_price()
            if event:
                yield event
            time.sleep(5)  # Poll every 5 seconds
