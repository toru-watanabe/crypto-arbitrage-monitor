"""Base scraper interface."""

from abc import ABC, abstractmethod
from typing import List
from src.models import PriceData


class BaseScraper(ABC):
    """Abstract base class for exchange scrapers."""
    
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
    
    @abstractmethod
    async def fetch_price(self, symbol: str) -> PriceData:
        """
        Fetch price for a single symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'ETH')
        
        Returns:
            PriceData object with price information
        """
        pass
    
    @abstractmethod
    async def fetch_all_prices(self, symbols: List[str]) -> List[PriceData]:
        """
        Fetch prices for multiple symbols.
        
        Args:
            symbols: List of trading symbols
        
        Returns:
            List of PriceData objects
        """
        pass
    
    def format_symbol(self, symbol: str) -> str:
        """
        Format symbol for the exchange.
        Default: SYMBOL + USDT (e.g., BTC -> BTCUSDT)
        
        Args:
            symbol: Base symbol (e.g., 'BTC')
        
        Returns:
            Formatted symbol for the exchange
        """
        return f"{symbol}USDT"
