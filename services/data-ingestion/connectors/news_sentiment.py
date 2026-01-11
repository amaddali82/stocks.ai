"""
News and Sentiment Data Connector
Fetches and analyzes news, sentiment, and M&A events
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json

import requests
import finnhub

logger = logging.getLogger(__name__)


class NewsSentimentConnector:
    """Connector for news, sentiment, and event data"""
    
    def __init__(self, finnhub_api_key: str, alpha_vantage_key: str,
                 kafka_producer, redis_cache):
        self.finnhub_key = finnhub_api_key
        self.alpha_vantage_key = alpha_vantage_key
        self.kafka_producer = kafka_producer
        self.redis_cache = redis_cache
        
        # Initialize Finnhub client
        if self.finnhub_key:
            self.finnhub_client = finnhub.Client(api_key=finnhub_api_key)
        else:
            self.finnhub_client = None
            logger.warning("No Finnhub API key - news/sentiment disabled")
        
        # Symbols to track
        self.tracked_symbols = self._load_tracked_symbols()
        
        logger.info(f"News Sentiment Connector initialized for {len(self.tracked_symbols)} symbols")
    
    def _load_tracked_symbols(self) -> List[str]:
        """Load symbols to track for news/sentiment"""
        # Should be loaded from config - using defaults for now
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
            'JPM', 'BAC', 'GS', 'JNJ', 'UNH', 'PFE',
            'SPY', 'QQQ', 'DIA'
        ]
    
    async def stream_news_realtime(self):
        """Stream real-time news articles"""
        if not self.finnhub_client:
            logger.warning("No Finnhub client - skipping news stream")
            return
        
        logger.info("Starting real-time news stream...")
        
        while True:
            try:
                # Fetch market news
                general_news = self.finnhub_client.general_news('general', min_id=0)
                
                for article in general_news[:20]:  # Latest 20 articles
                    data = {
                        'headline': article.get('headline'),
                        'summary': article.get('summary'),
                        'source': article.get('source'),
                        'url': article.get('url'),
                        'category': article.get('category'),
                        'timestamp': datetime.fromtimestamp(article.get('datetime', 0)).isoformat(),
                        'symbols': article.get('related', '').split(',') if article.get('related') else [],
                        'sentiment': self._analyze_sentiment(article.get('headline', '')),
                        'type': 'general_news'
                    }
                    
                    self.kafka_producer.send_message(
                        topic='news.general',
                        key=str(article.get('id', '')),
                        value=data
                    )
                
                # Fetch company-specific news
                for symbol in self.tracked_symbols:
                    try:
                        company_news = self.finnhub_client.company_news(
                            symbol,
                            _from=(datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d'),
                            to=datetime.now().strftime('%Y-%m-%d')
                        )
                        
                        for article in company_news[:10]:
                            data = {
                                'symbol': symbol,
                                'headline': article.get('headline'),
                                'summary': article.get('summary'),
                                'source': article.get('source'),
                                'url': article.get('url'),
                                'timestamp': datetime.fromtimestamp(article.get('datetime', 0)).isoformat(),
                                'sentiment': self._analyze_sentiment(article.get('headline', '')),
                                'type': 'company_news'
                            }
                            
                            self.kafka_producer.send_message(
                                topic='news.company',
                                key=symbol,
                                value=data
                            )
                            
                            # Cache latest news for each symbol
                            cache_key = f"news:{symbol}:latest"
                            self.redis_cache.lpush(cache_key, json.dumps(data))
                            self.redis_cache.ltrim(cache_key, 0, 99)  # Keep latest 100
                        
                        await asyncio.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"Error fetching news for {symbol}: {e}")
                
                # Wait 5 minutes before next fetch
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in news stream: {e}")
                await asyncio.sleep(60)
    
    async def fetch_sentiment_scores(self):
        """Fetch and compute sentiment scores"""
        if not self.finnhub_client:
            return
        
        logger.info("Starting sentiment score fetcher...")
        
        while True:
            try:
                for symbol in self.tracked_symbols:
                    # Fetch news sentiment from Finnhub
                    sentiment_data = self.finnhub_client.news_sentiment(symbol)
                    
                    if sentiment_data:
                        data = {
                            'symbol': symbol,
                            'sentiment_score': sentiment_data.get('sentiment', {}).get('score', 0),
                            'positive': sentiment_data.get('sentiment', {}).get('positive', 0),
                            'negative': sentiment_data.get('sentiment', {}).get('negative', 0),
                            'neutral': sentiment_data.get('sentiment', {}).get('neutral', 0),
                            'buzz': sentiment_data.get('buzz', {}).get('articlesInLastWeek', 0),
                            'timestamp': datetime.now().isoformat(),
                            'source': 'finnhub'
                        }
                        
                        self.kafka_producer.send_message(
                            topic='sentiment.scores',
                            key=symbol,
                            value=data
                        )
                        
                        # Cache sentiment
                        self.redis_cache.set(
                            f"sentiment:{symbol}",
                            json.dumps(data),
                            expiry=3600  # 1 hour
                        )
                    
                    await asyncio.sleep(2)  # Rate limiting
                
                logger.info(f"Fetched sentiment for {len(self.tracked_symbols)} symbols")
                
                # Wait 1 hour before next fetch
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error fetching sentiment: {e}")
                await asyncio.sleep(300)
    
    async def fetch_ma_events(self):
        """Fetch M&A and corporate events"""
        if not self.finnhub_client:
            return
        
        logger.info("Starting M&A events fetcher...")
        
        while True:
            try:
                # Fetch merger & acquisition news
                from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                to_date = datetime.now().strftime('%Y-%m-%d')
                
                ma_news = self.finnhub_client.merger_country(from_date, to_date)
                
                for event in ma_news:
                    data = {
                        'acquirer': event.get('acquirer'),
                        'target': event.get('target'),
                        'value': event.get('value'),
                        'announced_date': event.get('announcedDate'),
                        'status': event.get('status'),
                        'description': event.get('description'),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'merger_acquisition'
                    }
                    
                    self.kafka_producer.send_message(
                        topic='events.ma',
                        key=event.get('id', ''),
                        value=data
                    )
                
                # Fetch earnings calendar
                for symbol in self.tracked_symbols:
                    try:
                        earnings = self.finnhub_client.earnings_calendar(
                            symbol=symbol,
                            _from=from_date,
                            to=to_date
                        )
                        
                        for earning in earnings.get('earningsCalendar', []):
                            data = {
                                'symbol': symbol,
                                'date': earning.get('date'),
                                'eps_estimate': earning.get('epsEstimate'),
                                'eps_actual': earning.get('epsActual'),
                                'revenue_estimate': earning.get('revenueEstimate'),
                                'revenue_actual': earning.get('revenueActual'),
                                'timestamp': datetime.now().isoformat(),
                                'type': 'earnings'
                            }
                            
                            self.kafka_producer.send_message(
                                topic='events.earnings',
                                key=symbol,
                                value=data
                            )
                        
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error fetching earnings for {symbol}: {e}")
                
                logger.info("Fetched M&A and earnings events")
                
                # Wait 6 hours before next fetch
                await asyncio.sleep(21600)
                
            except Exception as e:
                logger.error(f"Error fetching M&A events: {e}")
                await asyncio.sleep(1800)
    
    def _analyze_sentiment(self, text: str) -> float:
        """Quick sentiment analysis using keyword matching (placeholder)"""
        # This is a simple placeholder - should use VADER or FinBERT
        positive_words = ['growth', 'profit', 'gain', 'surge', 'rally', 'bullish', 'strong']
        negative_words = ['loss', 'decline', 'fall', 'drop', 'weak', 'bearish', 'crisis']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    async def close(self):
        """Close all connections"""
        logger.info("Closing News Sentiment Connector...")
