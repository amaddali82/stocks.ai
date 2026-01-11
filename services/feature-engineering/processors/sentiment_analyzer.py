"""
Sentiment Analyzer using VADER and FinBERT
"""

import logging
from typing import Dict, List
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyze sentiment from news and social media"""
    
    def __init__(self, db_writer, redis_cache):
        self.db_writer = db_writer
        self.redis_cache = redis_cache
        
        # Initialize VADER
        self.vader = SentimentIntensityAnalyzer()
        
        # Initialize FinBERT
        try:
            self.finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            self.finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
            self.finbert_enabled = True
            logger.info("FinBERT model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load FinBERT: {e}")
            self.finbert_enabled = False
        
        logger.info("Sentiment Analyzer initialized")
    
    async def process_news(self, data: Dict):
        """Process news article and extract sentiment"""
        try:
            headline = data.get('headline', '')
            summary = data.get('summary', '')
            symbol = data.get('symbol')
            
            # Combine headline and summary
            text = f"{headline}. {summary}" if summary else headline
            
            # VADER sentiment (fast, rule-based)
            vader_scores = self.vader.polarity_scores(text)
            
            # FinBERT sentiment (deep learning, more accurate)
            finbert_scores = self._get_finbert_sentiment(text) if self.finbert_enabled else {}
            
            # Combine scores
            sentiment_features = {
                'symbol': symbol,
                'timestamp': data.get('timestamp'),
                'source': data.get('source'),
                'headline': headline[:500],  # Truncate
                'vader_positive': vader_scores['pos'],
                'vader_negative': vader_scores['neg'],
                'vader_neutral': vader_scores['neu'],
                'vader_compound': vader_scores['compound'],
                'finbert_positive': finbert_scores.get('positive', 0),
                'finbert_negative': finbert_scores.get('negative', 0),
                'finbert_neutral': finbert_scores.get('neutral', 0),
                'combined_sentiment': self._combine_sentiments(vader_scores, finbert_scores)
            }
            
            # Write to database
            await self.db_writer.write_features('sentiment_features', sentiment_features)
            
            # Update aggregated sentiment in cache
            self._update_aggregated_sentiment(symbol, sentiment_features)
            
            logger.debug(f"Analyzed sentiment for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing sentiment: {e}")
    
    def _get_finbert_sentiment(self, text: str) -> Dict:
        """Get sentiment using FinBERT"""
        try:
            # Tokenize
            inputs = self.finbert_tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            
            # Get predictions
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Extract scores
            scores = predictions[0].tolist()
            
            return {
                'positive': scores[0],
                'negative': scores[1],
                'neutral': scores[2]
            }
            
        except Exception as e:
            logger.error(f"FinBERT error: {e}")
            return {}
    
    def _combine_sentiments(self, vader_scores: Dict, finbert_scores: Dict) -> float:
        """Combine VADER and FinBERT scores"""
        # Weighted average (FinBERT has higher weight if available)
        if finbert_scores:
            vader_sentiment = vader_scores['compound']
            finbert_sentiment = finbert_scores['positive'] - finbert_scores['negative']
            
            # 30% VADER, 70% FinBERT
            combined = 0.3 * vader_sentiment + 0.7 * finbert_sentiment
        else:
            combined = vader_scores['compound']
        
        return combined
    
    def _update_aggregated_sentiment(self, symbol: str, sentiment_features: Dict):
        """Update rolling sentiment aggregate in Redis"""
        key = f"sentiment_agg:{symbol}"
        
        # Get recent sentiments
        recent = self.redis_cache.get_recent_sentiments(symbol, limit=20)
        recent.append(sentiment_features['combined_sentiment'])
        
        # Compute aggregates
        avg_sentiment = sum(recent) / len(recent) if recent else 0
        
        # Cache
        self.redis_cache.set(
            key,
            {
                'avg_sentiment_20': avg_sentiment,
                'latest_sentiment': sentiment_features['combined_sentiment'],
                'num_articles': len(recent)
            }
        )
