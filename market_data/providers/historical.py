"""
Historical Market Data Provider
Implements CSV-based historical data replay for demos and testing
"""
from typing import Optional, Iterator
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path
from .base import BaseMarketDataProvider, MarketEvent


class HistoricalProvider(BaseMarketDataProvider):
    """
    Historical data provider for replay mode
    
    Reads from CSV file and replays events at configurable speed
    Perfect for demos, testing, and development
    """
    
    def _validate_config(self, **kwargs) -> None:
        """Validate historical data file path"""
        self.data_path = kwargs.get("data_path", "data/historical_prices.csv")
        self.replay_speed = kwargs.get("replay_speed", 1.0)  # 1.0 = real-time
        
        self.data: Optional[pd.DataFrame] = None
        self.current_index = 0
    
    def connect(self) -> bool:
        """Load historical data from CSV"""
        try:
            path = Path(self.data_path)
            
            if not path.exists():
                print(f"Historical data file not found: {self.data_path}")
                return False
            
            # Read CSV
            self.data = pd.read_csv(path)
            
            # Validate required columns
            required_cols = ["timestamp", "price"]
            if not all(col in self.data.columns for col in required_cols):
                print(f"CSV must contain columns: {required_cols}")
                return False
            
            # Add instrument_id if not present
            if "instrument_id" not in self.data.columns:
                self.data["instrument_id"] = self.instrument_id
            
            # Sort by timestamp
            self.data = self.data.sort_values("timestamp").reset_index(drop=True)
            
            self.is_connected = True
            print(f"Loaded {len(self.data)} historical data points")
            return True
            
        except Exception as e:
            print(f"Historical data load error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Clear data"""
        self.data = None
        self.current_index = 0
        self.is_connected = False
    
    def get_latest_price(self) -> Optional[MarketEvent]:
        """
        Get the current price in the replay sequence
        """
        if self.data is None or self.current_index >= len(self.data):
            return None
        
        try:
            row = self.data.iloc[self.current_index]
            
            return MarketEvent(
                timestamp=row["timestamp"],
                instrument_id=str(row["instrument_id"]),
                price=float(row["price"])
            )
        except Exception as e:
            print(f"Historical fetch error: {e}")
            return None
    
    def stream_prices(self) -> Iterator[MarketEvent]:
        """
        Stream historical prices with time-based replay
        
        Respects original time intervals scaled by replay_speed
        """
        if self.data is None:
            return
        
        prev_timestamp = None
        
        for idx in range(len(self.data)):
            self.current_index = idx
            row = self.data.iloc[idx]
            
            # Calculate delay based on original time intervals
            if prev_timestamp is not None and self.replay_speed > 0:
                try:
                    curr_time = pd.to_datetime(row["timestamp"])
                    prev_time = pd.to_datetime(prev_timestamp)
                    time_diff = (curr_time - prev_time).total_seconds()
                    
                    # Scale by replay speed (2.0 = 2x faster, 0.5 = 2x slower)
                    delay = time_diff / self.replay_speed
                    
                    if delay > 0:
                        time.sleep(min(delay, 60))  # Cap at 60 seconds
                        
                except Exception:
                    time.sleep(1.0)  # Default 1 second delay
            
            prev_timestamp = row["timestamp"]
            
            event = MarketEvent(
                timestamp=row["timestamp"],
                instrument_id=str(row["instrument_id"]),
                price=float(row["price"])
            )
            
            yield event
    
    def reset_replay(self) -> None:
        """Reset replay to beginning"""
        self.current_index = 0
    
    def seek_to_time(self, target_time: str) -> bool:
        """
        Seek to specific timestamp in replay
        
        Args:
            target_time: ISO-8601 timestamp string
        
        Returns:
            True if found, False otherwise
        """
        if self.data is None:
            return False
        
        try:
            target_dt = pd.to_datetime(target_time)
            timestamps = pd.to_datetime(self.data["timestamp"])
            
            # Find closest timestamp
            idx = (timestamps - target_dt).abs().argmin()
            self.current_index = idx
            return True
            
        except Exception as e:
            print(f"Seek error: {e}")
            return False
