"""
Feature Engineering Service - Main Entry Point
Consumes market data and computes technical indicators, sentiment features, etc.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

from consumers.kafka_consumer import KafkaDataConsumer
from processors.technical_indicators import TechnicalIndicatorProcessor
from processors.sentiment_analyzer import SentimentAnalyzer
from processors.event_processor import EventProcessor
from storage.timescaledb_writer import TimescaleDBWriter
from storage.redis_cache import RedisFeatureCache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureEngineeringService:
    """Main service for feature engineering"""
    
    def __init__(self):
        # Initialize storage
        self.db_writer = TimescaleDBWriter(
            host=os.getenv('TIMESCALEDB_HOST', 'timescaledb'),
            port=int(os.getenv('TIMESCALEDB_PORT', 5432)),
            user=os.getenv('TIMESCALEDB_USER', 'trading_user'),
            password=os.getenv('TIMESCALEDB_PASSWORD', 'trading_pass'),
            database=os.getenv('TIMESCALEDB_DB', 'trading_db')
        )
        
        self.redis_cache = RedisFeatureCache(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379))
        )
        
        # Initialize processors
        self.technical_processor = TechnicalIndicatorProcessor(
            db_writer=self.db_writer,
            redis_cache=self.redis_cache
        )
        
        self.sentiment_analyzer = SentimentAnalyzer(
            db_writer=self.db_writer,
            redis_cache=self.redis_cache
        )
        
        self.event_processor = EventProcessor(
            db_writer=self.db_writer,
            redis_cache=self.redis_cache
        )
        
        # Initialize Kafka consumers
        self.kafka_consumer = KafkaDataConsumer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092'),
            technical_processor=self.technical_processor,
            sentiment_analyzer=self.sentiment_analyzer,
            event_processor=self.event_processor
        )
        
        logger.info("Feature Engineering Service initialized")
    
    async def start(self):
        """Start the service"""
        logger.info("Starting feature engineering service...")
        
        # Initialize database schema
        await self.db_writer.initialize_schema()
        
        # Start consuming and processing
        await self.kafka_consumer.start_consuming()
    
    async def stop(self):
        """Graceful shutdown"""
        logger.info("Stopping feature engineering service...")
        await self.kafka_consumer.stop()
        await self.db_writer.close()
        self.redis_cache.close()
        logger.info("Feature engineering service stopped")


async def main():
    """Main entry point"""
    service = FeatureEngineeringService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
