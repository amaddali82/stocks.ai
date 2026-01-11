"""
Redis Cache for fast data access
"""

import logging
import json
from typing import Any, Optional, List
import redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache wrapper for market data"""
    
    def __init__(self, host: str, port: int, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Redis client"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis client connected to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.client = None
    
    def set(self, key: str, value: str, expiry: Optional[int] = None):
        """Set a key-value pair with optional expiry (seconds)"""
        if not self.client:
            return False
        
        try:
            if expiry:
                self.client.setex(key, expiry, value)
            else:
                self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.client:
            return None
        
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for {key}: {e}")
            return False
    
    def lpush(self, key: str, value: str) -> bool:
        """Push value to list (left)"""
        if not self.client:
            return False
        
        try:
            self.client.lpush(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis LPUSH error for {key}: {e}")
            return False
    
    def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get range from list"""
        if not self.client:
            return []
        
        try:
            return self.client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Redis LRANGE error for {key}: {e}")
            return []
    
    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range"""
        if not self.client:
            return False
        
        try:
            self.client.ltrim(key, start, end)
            return True
        except Exception as e:
            logger.error(f"Redis LTRIM error for {key}: {e}")
            return False
    
    def hset(self, name: str, key: str, value: str) -> bool:
        """Set hash field"""
        if not self.client:
            return False
        
        try:
            self.client.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Redis HSET error for {name}:{key}: {e}")
            return False
    
    def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field"""
        if not self.client:
            return None
        
        try:
            return self.client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET error for {name}:{key}: {e}")
            return None
    
    def hgetall(self, name: str) -> dict:
        """Get all hash fields"""
        if not self.client:
            return {}
        
        try:
            return self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis HGETALL error for {name}: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        if not self.client:
            return False
        
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            logger.info("Closing Redis client...")
            self.client.close()
