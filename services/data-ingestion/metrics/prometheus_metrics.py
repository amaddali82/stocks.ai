"""
Prometheus metrics exporter for monitoring
"""

import logging
from prometheus_client import start_http_server, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class MetricsExporter:
    """Prometheus metrics for data ingestion service"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        
        # Define metrics
        self.messages_sent = Counter(
            'data_ingestion_messages_sent_total',
            'Total messages sent to Kafka',
            ['topic', 'source']
        )
        
        self.messages_failed = Counter(
            'data_ingestion_messages_failed_total',
            'Total messages that failed to send',
            ['topic', 'source']
        )
        
        self.cache_operations = Counter(
            'data_ingestion_cache_operations_total',
            'Total Redis cache operations',
            ['operation', 'status']
        )
        
        self.websocket_connections = Gauge(
            'data_ingestion_websocket_connections',
            'Active WebSocket connections',
            ['source']
        )
        
        self.message_latency = Histogram(
            'data_ingestion_message_latency_seconds',
            'Message processing latency',
            ['source']
        )
        
        self.health_status = Gauge(
            'data_ingestion_health_status',
            'Health status (1=healthy, 0=unhealthy)'
        )
        
        logger.info(f"Metrics exporter initialized on port {port}")
    
    def start(self):
        """Start Prometheus HTTP server"""
        try:
            start_http_server(self.port)
            logger.info(f"Metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    
    def record_message_sent(self, topic: str, source: str):
        """Record a successful message send"""
        self.messages_sent.labels(topic=topic, source=source).inc()
    
    def record_message_failed(self, topic: str, source: str):
        """Record a failed message send"""
        self.messages_failed.labels(topic=topic, source=source).inc()
    
    def record_cache_operation(self, operation: str, status: str):
        """Record a cache operation"""
        self.cache_operations.labels(operation=operation, status=status).inc()
    
    def set_websocket_connections(self, source: str, count: int):
        """Set WebSocket connection count"""
        self.websocket_connections.labels(source=source).set(count)
    
    def record_message_latency(self, source: str, latency: float):
        """Record message processing latency"""
        self.message_latency.labels(source=source).observe(latency)
    
    def record_health_status(self, status: int):
        """Record health status"""
        self.health_status.set(status)
