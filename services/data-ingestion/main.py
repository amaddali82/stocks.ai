"""
Data Ingestion Service - Main Entry Point
Streams real-time market data, options, and news from multiple sources
"""

import os
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from connectors.us_market import USMarketConnector
from connectors.india_market import IndiaMarketConnector
from connectors.news_sentiment import NewsSentimentConnector
from streaming.kafka_producer import KafkaStreamProducer
from streaming.redis_cache import RedisCache
from metrics.prometheus_metrics import MetricsExporter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataIngestionService:
    """Main service orchestrator for data ingestion"""
    
    def __init__(self):
        self.kafka_producer = KafkaStreamProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
        )
        self.redis_cache = RedisCache(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379))
        )
        self.metrics = MetricsExporter(port=8000)
        
        # Initialize connectors
        self.us_market = USMarketConnector(
            polygon_api_key=os.getenv('POLYGON_API_KEY'),
            alpha_vantage_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
            kafka_producer=self.kafka_producer,
            redis_cache=self.redis_cache
        )
        
        self.india_market = IndiaMarketConnector(
            zerodha_api_key=os.getenv('ZERODHA_API_KEY'),
            zerodha_api_secret=os.getenv('ZERODHA_API_SECRET'),
            zerodha_access_token=os.getenv('ZERODHA_ACCESS_TOKEN'),
            kafka_producer=self.kafka_producer,
            redis_cache=self.redis_cache
        )
        
        self.news_sentiment = NewsSentimentConnector(
            finnhub_api_key=os.getenv('FINNHUB_API_KEY'),
            alpha_vantage_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
            kafka_producer=self.kafka_producer,
            redis_cache=self.redis_cache
        )
        
        logger.info("Data Ingestion Service initialized")
    
    async def start(self):
        """Start all data ingestion streams"""
        logger.info("Starting data ingestion service...")
        
        # Start metrics exporter
        self.metrics.start()
        
        # Create tasks for each data stream
        tasks = [
            # US Market streams
            self.us_market.stream_stocks_realtime(),
            self.us_market.stream_options_realtime(),
            self.us_market.fetch_open_interest(),
            
            # India Market streams
            self.india_market.stream_stocks_realtime(),
            self.india_market.stream_options_realtime(),
            self.india_market.fetch_open_interest(),
            
            # News and Sentiment
            self.news_sentiment.stream_news_realtime(),
            self.news_sentiment.fetch_sentiment_scores(),
            self.news_sentiment.fetch_ma_events(),
            
            # Health check
            self.health_check_loop()
        ]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def health_check_loop(self):
        """Periodic health check"""
        while True:
            try:
                # Check Kafka connection
                kafka_healthy = self.kafka_producer.health_check()
                
                # Check Redis connection
                redis_healthy = self.redis_cache.health_check()
                
                if kafka_healthy and redis_healthy:
                    logger.info("Health check: All systems operational")
                    self.metrics.record_health_status(1)
                else:
                    logger.warning("Health check: Some systems down")
                    self.metrics.record_health_status(0)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Graceful shutdown"""
        logger.info("Stopping data ingestion service...")
        
        # Close connections
        await self.us_market.close()
        await self.india_market.close()
        await self.news_sentiment.close()
        self.kafka_producer.close()
        self.redis_cache.close()
        
        logger.info("Data ingestion service stopped")


async def main():
    """Main entry point"""
    service = DataIngestionService()
    
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
