"""Redis client for caching real-time price data."""

import json
import redis
from typing import List, Optional
from datetime import timedelta
from src.models import PriceData
from src.config import settings


class RedisClient:
    """Client for interacting with Redis cache."""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def _price_key(self, exchange: str, symbol: str) -> str:
        """Generate Redis key for price data."""
        return f"price:{exchange}:{symbol}"
    
    def set_price(self, price_data: PriceData, ttl: int = 300):
        """
        Store price data in Redis with TTL.
        
        Args:
            price_data: PriceData object to store
            ttl: Time to live in seconds (default: 5 minutes)
        """
        key = self._price_key(price_data.exchange, price_data.symbol)
        value = price_data.model_dump_json()
        self.client.setex(key, ttl, value)
    
    def get_price(self, exchange: str, symbol: str) -> Optional[PriceData]:
        """
        Retrieve price data from Redis.
        
        Args:
            exchange: Exchange name
            symbol: Trading symbol
        
        Returns:
            PriceData object or None if not found
        """
        key = self._price_key(exchange, symbol)
        value = self.client.get(key)
        
        if value:
            return PriceData.model_validate_json(value)
        return None
    
    def set_prices_batch(self, prices: List[PriceData], ttl: int = 300):
        """
        Store multiple price data in Redis.
        
        Args:
            prices: List of PriceData objects
            ttl: Time to live in seconds
        """
        pipe = self.client.pipeline()
        for price in prices:
            key = self._price_key(price.exchange, price.symbol)
            value = price.model_dump_json()
            pipe.setex(key, ttl, value)
        pipe.execute()
    
    def get_all_prices_for_symbol(self, symbol: str) -> List[PriceData]:
        """
        Get prices from all exchanges for a specific symbol.
        
        Args:
            symbol: Trading symbol
        
        Returns:
            List of PriceData objects from all exchanges
        """
        pattern = f"price:*:{symbol}"
        keys = self.client.keys(pattern)
        
        prices = []
        for key in keys:
            value = self.client.get(key)
            if value:
                prices.append(PriceData.model_validate_json(value))
        
        return prices
    
    def get_all_latest_prices(self) -> List[PriceData]:
        """
        Get all latest prices from cache.
        
        Returns:
            List of all cached PriceData objects
        """
        pattern = "price:*"
        keys = self.client.keys(pattern)
        
        prices = []
        for key in keys:
            value = self.client.get(key)
            if value:
                prices.append(PriceData.model_validate_json(value))
        
        return prices
    
    def clear_all(self):
        """Clear all price data from Redis."""
        pattern = "price:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)
    
    def health_check(self) -> bool:
        """Check if Redis is accessible."""
        try:
            return self.client.ping()
        except Exception as e:
            print(f"Redis health check failed: {e}")
            return False


# Test function
if __name__ == "__main__":
    from datetime import datetime
    
    client = RedisClient()
    
    # Health check
    print(f"Redis health: {client.health_check()}")
    
    # Test storing and retrieving price
    test_price = PriceData(
        exchange="binance",
        symbol="BTCUSDT",
        price=45000.0,
        timestamp=datetime.utcnow()
    )
    
    client.set_price(test_price)
    retrieved = client.get_price("binance", "BTCUSDT")
    print(f"Stored and retrieved: {retrieved}")
