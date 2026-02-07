"""
Intrinio Market Data Provider
Implements market data ingestion via Intrinio API
"""
from typing import Optional, Iterator
import requests
import time
from datetime import datetime
from .base import BaseMarketDataProvider, MarketEvent


class IntrinioProvider(BaseMarketDataProvider):
    """
    Intrinio real-time financial data provider
    
    API Documentation: https://docs.intrinio.com/
    """
    
    BASE_URL = "https://api-v2.intrinio.com"
    
    def _validate_config(self, **kwargs) -> None:
        """Validate Intrinio API key"""
        self.api_key = kwargs.get("api_key", "")
        if not self.api_key:
            raise ValueError("Intrinio API key is required")
        
        self.session = requests.Session()
        self.session.auth = (self.api_key, '')  # Basic auth with API key as username
        self.last_request_time = 0
        self.rate_limit_delay = 0.2  # Conservative rate limiting
    
    def connect(self) -> bool:
        """Test API connectivity"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/securities/{self.instrument_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                self.is_connected = True
                return True
            else:
                print(f"Intrinio connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Intrinio connection error: {e}")
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
        Fetch latest price from Intrinio
        """
        try:
            self._respect_rate_limit()
            
            # Get real-time price
            response = self.session.get(
                f"{self.BASE_URL}/securities/{self.instrument_id}/prices/realtime",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                price = data.get("last_price", 0.0)
                timestamp_str = data.get("updated_on", datetime.now().isoformat())
                
                # Ensure ISO-8601 format
                if 'T' not in timestamp_str:
                    timestamp_str = datetime.now().isoformat()
                
                return MarketEvent(
                    timestamp=timestamp_str,
                    instrument_id=self.instrument_id,
                    price=float(price)
                )
            
            return None
            
        except Exception as e:
            print(f"Intrinio fetch error: {e}")
            return None
    
    def stream_prices(self) -> Iterator[MarketEvent]:
        """
        Stream prices by polling at regular intervals
        """
        while self.is_connected:
            event = self.get_latest_price()
            if event:
                yield event
            time.sleep(5)  # Poll every 5 seconds
