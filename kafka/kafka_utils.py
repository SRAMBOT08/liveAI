"""
Kafka Utilities
Helper functions for Kafka operations
"""
import json
from typing import Dict, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaError


def create_kafka_producer(bootstrap_servers: str, **config) -> KafkaProducer:
    """
    Create a configured Kafka producer
    
    Args:
        bootstrap_servers: Kafka broker address
        **config: Additional producer configuration
    
    Returns:
        KafkaProducer instance
    """
    default_config = {
        'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
        'key_serializer': lambda k: k.encode('utf-8') if k else None,
        'acks': 'all',
        'retries': 3,
        'max_in_flight_requests_per_connection': 1,
        'compression_type': 'gzip'
    }
    
    # Merge with custom config
    default_config.update(config)
    
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        **default_config
    )


def create_kafka_consumer(
    bootstrap_servers: str,
    topics: list,
    group_id: str,
    **config
) -> KafkaConsumer:
    """
    Create a configured Kafka consumer
    
    Args:
        bootstrap_servers: Kafka broker address
        topics: List of topics to subscribe to
        group_id: Consumer group ID
        **config: Additional consumer configuration
    
    Returns:
        KafkaConsumer instance
    """
    default_config = {
        'value_deserializer': lambda v: json.loads(v.decode('utf-8')),
        'key_deserializer': lambda k: k.decode('utf-8') if k else None,
        'auto_offset_reset': 'latest',
        'enable_auto_commit': True,
        'group_id': group_id
    }
    
    # Merge with custom config
    default_config.update(config)
    
    return KafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        **default_config
    )


def ensure_topic_exists(
    bootstrap_servers: str,
    topic_name: str,
    num_partitions: int = 3,
    replication_factor: int = 1
) -> bool:
    """
    Ensure a Kafka topic exists, create if it doesn't
    
    Args:
        bootstrap_servers: Kafka broker address
        topic_name: Name of the topic
        num_partitions: Number of partitions
        replication_factor: Replication factor
    
    Returns:
        True if topic exists or was created, False on error
    """
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id='liveai_admin'
        )
        
        topic = NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor
        )
        
        try:
            admin_client.create_topics([topic], validate_only=False)
            print(f"Created topic: {topic_name}")
        except TopicAlreadyExistsError:
            print(f"Topic already exists: {topic_name}")
        
        admin_client.close()
        return True
        
    except Exception as e:
        print(f"Error ensuring topic exists: {e}")
        return False


def send_event(
    producer: KafkaProducer,
    topic: str,
    event: Dict,
    key: Optional[str] = None
) -> bool:
    """
    Send an event to Kafka
    
    Args:
        producer: KafkaProducer instance
        topic: Topic name
        event: Event data (will be JSON-serialized)
        key: Optional partition key
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        future = producer.send(topic, value=event, key=key)
        # Wait for acknowledgment (blocking)
        record_metadata = future.get(timeout=10)
        return True
        
    except KafkaError as e:
        print(f"Kafka send error: {e}")
        return False


def flush_producer(producer: KafkaProducer, timeout: int = 10) -> None:
    """
    Flush producer to ensure all messages are sent
    
    Args:
        producer: KafkaProducer instance
        timeout: Timeout in seconds
    """
    producer.flush(timeout=timeout)


def close_producer(producer: KafkaProducer, timeout: int = 10) -> None:
    """
    Gracefully close producer
    
    Args:
        producer: KafkaProducer instance
        timeout: Timeout in seconds
    """
    try:
        producer.flush(timeout=timeout)
        producer.close(timeout=timeout)
    except Exception as e:
        print(f"Error closing producer: {e}")
