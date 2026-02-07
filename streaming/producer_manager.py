"""
Kafka Producer Manager
Orchestrates market data provider selection and Kafka event publishing
"""
from typing import Optional, Dict
import threading
import time
from kafka import KafkaProducer

from config.settings import config, MarketDataProvider
from config.instruments import DEFAULT_FUTURES
from market_data.providers import (
    BaseMarketDataProvider,
    PolygonProvider,
    IntrinioProvider,
    TwelveDataProvider,
    HistoricalProvider
)
from .kafka_utils import (
    create_kafka_producer,
    ensure_topic_exists,
    send_event,
    close_producer
)


class ProducerManager:
    """
    Manages market data provider selection and Kafka event production
    
    Responsibilities:
    1. Instantiate correct market data provider based on config
    2. Handle provider failover
    3. Publish market events to Kafka
    4. Manage producer lifecycle
    
    Design: Provider-agnostic orchestration layer
    """
    
    def __init__(self):
        self.provider: Optional[BaseMarketDataProvider] = None
        self.producer: Optional[KafkaProducer] = None
        self.is_running = False
        self.publish_thread: Optional[threading.Thread] = None
        self.event_count = 0
        self.error_count = 0
        
    def initialize(self) -> bool:
        """
        Initialize producer and market data provider
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure Kafka topic exists
            topic_created = ensure_topic_exists(
                bootstrap_servers=config.kafka.bootstrap_servers,
                topic_name=config.kafka.topic_market_data,
                num_partitions=3,
                replication_factor=1
            )
            
            if not topic_created:
                print("Warning: Could not verify Kafka topic")
            
            # Create Kafka producer
            self.producer = create_kafka_producer(
                bootstrap_servers=config.kafka.bootstrap_servers,
                **config.kafka.producer_config
            )
            
            # Initialize market data provider
            success = self._initialize_provider(config.market_data_provider)
            
            if success:
                print(f"ProducerManager initialized with {config.market_data_provider.value} provider")
            
            return success
            
        except Exception as e:
            print(f"ProducerManager initialization error: {e}")
            return False
    
    def _initialize_provider(self, provider_type: MarketDataProvider) -> bool:
        """
        Initialize specific market data provider
        
        Args:
            provider_type: Provider to initialize
        
        Returns:
            True if successful, False otherwise
        """
        try:
            instrument_id = DEFAULT_FUTURES.symbol
            
            # Select provider based on configuration
            if provider_type == MarketDataProvider.POLYGON:
                self.provider = PolygonProvider(
                    instrument_id=instrument_id,
                    api_key=config.market_data_providers.polygon_api_key
                )
            
            elif provider_type == MarketDataProvider.INTRINIO:
                self.provider = IntrinioProvider(
                    instrument_id=instrument_id,
                    api_key=config.market_data_providers.intrinio_api_key
                )
            
            elif provider_type == MarketDataProvider.TWELVE_DATA:
                self.provider = TwelveDataProvider(
                    instrument_id=instrument_id,
                    api_key=config.market_data_providers.twelve_data_api_key
                )
            
            elif provider_type == MarketDataProvider.HISTORICAL:
                self.provider = HistoricalProvider(
                    instrument_id=instrument_id,
                    data_path=config.market_data_providers.historical_data_path,
                    replay_speed=config.market_data_providers.historical_replay_speed_multiplier
                )
            
            else:
                print(f"Unknown provider type: {provider_type}")
                return False
            
            # Connect to provider
            return self.provider.connect()
            
        except Exception as e:
            print(f"Provider initialization error: {e}")
            return False
    
    def switch_provider(self, new_provider: MarketDataProvider) -> bool:
        """
        Switch to a different market data provider
        
        Args:
            new_provider: New provider to use
        
        Returns:
            True if successful, False otherwise
        """
        was_running = self.is_running
        
        # Stop current streaming if active
        if was_running:
            self.stop_streaming()
        
        # Disconnect old provider
        if self.provider:
            self.provider.disconnect()
        
        # Initialize new provider
        success = self._initialize_provider(new_provider)
        
        # Resume streaming if it was active
        if was_running and success:
            self.start_streaming()
        
        return success
    
    def start_streaming(self) -> bool:
        """
        Start streaming market data to Kafka
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            print("Streaming already active")
            return False
        
        if not self.provider or not self.producer:
            print("Provider or producer not initialized")
            return False
        
        self.is_running = True
        self.publish_thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.publish_thread.start()
        
        print("Started streaming market data to Kafka")
        return True
    
    def stop_streaming(self) -> None:
        """Stop streaming market data"""
        self.is_running = False
        
        if self.publish_thread:
            self.publish_thread.join(timeout=5)
        
        print("Stopped streaming market data")
    
    def _stream_worker(self) -> None:
        """
        Worker thread that streams data from provider to Kafka
        """
        try:
            for event in self.provider.stream_prices():
                if not self.is_running:
                    break
                
                # Publish to Kafka
                success = send_event(
                    producer=self.producer,
                    topic=config.kafka.topic_market_data,
                    event=event.to_dict(),
                    key=event.instrument_id
                )
                
                if success:
                    self.event_count += 1
                    if self.event_count % 10 == 0:
                        print(f"Published {self.event_count} events")
                else:
                    self.error_count += 1
                    print(f"Failed to publish event (errors: {self.error_count})")
                
        except Exception as e:
            print(f"Stream worker error: {e}")
            self.is_running = False
    
    def get_status(self) -> Dict:
        """
        Get current producer status
        
        Returns:
            Status dictionary
        """
        return {
            "is_running": self.is_running,
            "provider": config.market_data_provider.value,
            "provider_connected": self.provider.is_connected if self.provider else False,
            "events_published": self.event_count,
            "errors": self.error_count,
            "instrument": DEFAULT_FUTURES.symbol
        }
    
    def shutdown(self) -> None:
        """Graceful shutdown"""
        print("Shutting down ProducerManager...")
        
        self.stop_streaming()
        
        if self.provider:
            self.provider.disconnect()
        
        if self.producer:
            close_producer(self.producer)
        
        print("ProducerManager shutdown complete")


# Global producer manager instance
producer_manager = ProducerManager()
