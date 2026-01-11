"""
Kafka Producer for streaming data
"""

import logging
import json
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaStreamProducer:
    """Kafka producer wrapper for streaming market data"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer with retry logic"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5,
                compression_type='gzip',
                buffer_memory=33554432,  # 32MB buffer
                batch_size=16384,
                linger_ms=10  # Wait 10ms to batch messages
            )
            logger.info(f"Kafka producer connected to {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def send_message(self, topic: str, value: Dict[str, Any], key: Optional[str] = None):
        """Send a message to Kafka topic"""
        if not self.producer:
            logger.warning("Kafka producer not initialized")
            return
        
        try:
            future = self.producer.send(topic, value=value, key=key)
            
            # Optionally wait for confirmation (blocking)
            # record_metadata = future.get(timeout=10)
            
        except KafkaError as e:
            logger.error(f"Failed to send message to {topic}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending to Kafka: {e}")
    
    def flush(self):
        """Flush any pending messages"""
        if self.producer:
            self.producer.flush()
    
    def health_check(self) -> bool:
        """Check if Kafka producer is healthy"""
        if not self.producer:
            return False
        
        try:
            # Try to get cluster metadata
            self.producer._metadata.request_update()
            return True
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            logger.info("Closing Kafka producer...")
            self.producer.flush()
            self.producer.close()
