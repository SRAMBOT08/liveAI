"""
Global Configuration Settings
Production-grade configuration for LiveAI Real-Time Market Risk Intelligence Platform
"""
from dataclasses import dataclass
from typing import Literal
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()


class Mode(str, Enum):
    """Operating mode for the system"""
    HISTORICAL = "historical"
    LIVE = "live"


class MarketDataProvider(str, Enum):
    """Supported market data providers"""
    POLYGON = "polygon"
    INTRINIO = "intrinio"
    TWELVE_DATA = "twelve_data"
    HISTORICAL = "historical"


class GenAIProvider(str, Enum):
    """Supported GenAI providers"""
    OPENAI = "openai"
    GEMINI = "gemini"
    GROK = "grok"


@dataclass
class KafkaConfig:
    """Kafka connection configuration"""
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic_market_data: str = "market_data_events"
    topic_risk_events: str = "risk_events"
    producer_config: dict = None
    
    def __post_init__(self):
        if self.producer_config is None:
            self.producer_config = {
                'acks': 'all',
                'retries': 3,
                'max_in_flight_requests_per_connection': 1
            }


@dataclass
class PathwayConfig:
    """Pathway streaming engine configuration"""
    # State management
    state_checkpoint_interval_ms: int = 5000
    
    # Computation windows
    price_lookback_window: int = 100  # number of ticks
    
    # Performance
    worker_threads: int = 4


@dataclass
class RiskThresholds:
    """Risk detection thresholds"""
    # Greeks thresholds for event detection
    delta_change_threshold: float = 0.05  # 5% change
    gamma_change_threshold: float = 0.10  # 10% change
    theta_change_threshold: float = 0.05  # 5% change
    vega_change_threshold: float = 0.10  # 10% change
    
    # Risk score thresholds
    risk_score_min: float = 0.0
    risk_score_max: float = 100.0
    
    # Regime boundaries
    stable_max: float = 30.0  # 0-30: STABLE
    sensitive_max: float = 65.0  # 30-65: SENSITIVE
    # 65-100: FRAGILE
    
    # Shock scenarios
    shock_scenarios: list = None
    
    def __post_init__(self):
        if self.shock_scenarios is None:
            self.shock_scenarios = [0.01, 0.05, -0.01, -0.05]  # ±1%, ±5%


@dataclass
class MarketDataProviderConfig:
    """Market data provider API configurations"""
    polygon_api_key: str = os.getenv("POLYGON_API_KEY", "")
    intrinio_api_key: str = os.getenv("INTRINIO_API_KEY", "")
    twelve_data_api_key: str = os.getenv("TWELVE_DATA_API_KEY", "")
    
    # Historical data path
    historical_data_path: str = "data/historical_prices.csv"
    
    # Refresh rates
    live_refresh_rate_seconds: int = 5
    historical_replay_speed_multiplier: float = 1.0  # 1.0 = real-time


@dataclass
class GenAIProviderConfig:
    """GenAI provider API configurations"""
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4"
    
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = "gemini-1.5-pro"
    
    grok_api_key: str = os.getenv("GROK_API_KEY", "")
    grok_api_base: str = "https://api.x.ai/v1"
    grok_model: str = "grok-beta"
    
    # RAG configuration
    max_context_items: int = 10  # recent events to include
    temperature: float = 0.3  # low temperature for factual responses
    max_tokens: int = 300


@dataclass
class SystemConfig:
    """Master system configuration"""
    # Operating parameters
    mode: Mode = Mode.HISTORICAL
    market_data_provider: MarketDataProvider = MarketDataProvider.HISTORICAL
    genai_provider: GenAIProvider = GenAIProvider.OPENAI
    
    # Component configurations
    kafka: KafkaConfig = None
    pathway: PathwayConfig = None
    risk_thresholds: RiskThresholds = None
    market_data_providers: MarketDataProviderConfig = None
    genai_providers: GenAIProviderConfig = None
    
    def __post_init__(self):
        if self.kafka is None:
            self.kafka = KafkaConfig()
        if self.pathway is None:
            self.pathway = PathwayConfig()
        if self.risk_thresholds is None:
            self.risk_thresholds = RiskThresholds()
        if self.market_data_providers is None:
            self.market_data_providers = MarketDataProviderConfig()
        if self.genai_providers is None:
            self.genai_providers = GenAIProviderConfig()


# Global configuration instance
config = SystemConfig()


def update_mode(new_mode: Mode) -> None:
    """Update operating mode"""
    global config
    config.mode = new_mode


def update_market_data_provider(provider: MarketDataProvider) -> None:
    """Update market data provider"""
    global config
    config.market_data_provider = provider


def update_genai_provider(provider: GenAIProvider) -> None:
    """Update GenAI provider"""
    global config
    config.genai_provider = provider
