"""Configuration management for the arbitrage monitoring system."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Bybit API
    BYBIT_API_KEY: str = ""
    BYBIT_API_SECRET: str = ""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # TimescaleDB
    POSTGRES_HOST: str = "timescaledb"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "arbitrage_monitor"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres123"
    
    # Coins to monitor
    COINS: str = "BTC,ETH,BNB,SOL,TRX,DOGE,ADA"
    
    # Exchange fees (in percentage)
    BYBIT_FEE: float = 0.01
    BINANCE_FEE: float = 0.01
    KUCOIN_FEE: float = 0.01
    
    # Arbitrage threshold
    MIN_PROFIT_THRESHOLD: float = 0.02
    
    # Scraping interval
    SCRAPE_INTERVAL: int = 30
    
    # Dashboard
    DASHBOARD_HOST: str = "0.0.0.0"
    DASHBOARD_PORT: int = 8050
    DASHBOARD_DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore Airflow and other extra environment variables
    
    @property
    def coin_list(self) -> List[str]:
        """Get list of coins to monitor."""
        return [coin.strip() for coin in self.COINS.split(",")]
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def get_exchange_fee(self, exchange: str) -> float:
        """Get fee for a specific exchange."""
        fees = {
            "bybit": self.BYBIT_FEE,
            "binance": self.BINANCE_FEE,
            "kucoin": self.KUCOIN_FEE,
        }
        return fees.get(exchange.lower(), 0.01)


# Global settings instance
settings = Settings()
