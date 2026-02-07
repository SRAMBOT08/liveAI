"""
Pathway Kafka Ingestion
Handles streaming ingestion from Kafka into Pathway tables
"""
import pathway as pw
from typing import Optional
import json

from config.settings import config
from .schemas import MarketEventSchema


def create_kafka_input() -> pw.Table:
    """
    Create Pathway input connector for Kafka market data
    
    Returns:
        Pathway table with streaming market events
    """
    
    # Kafka input connector configuration
    rdkafka_settings = {
        "bootstrap.servers": config.kafka.bootstrap_servers,
        "group.id": "pathway_liveai_consumer",
        "auto.offset.reset": "latest",
        "enable.auto.commit": "true"
    }
    
    # Create Pathway input from Kafka
    market_events = pw.io.kafka.read(
        rdkafka_settings,
        topic=config.kafka.topic_market_data,
        format="json",
        schema=MarketEventSchema,
        autocommit_duration_ms=1000
    )
    
    return market_events


def parse_market_event(event_json: str) -> Optional[dict]:
    """
    Parse market event JSON string
    
    Args:
        event_json: JSON string from Kafka
    
    Returns:
        Parsed dictionary or None if invalid
    """
    try:
        return json.loads(event_json)
    except json.JSONDecodeError:
        return None
