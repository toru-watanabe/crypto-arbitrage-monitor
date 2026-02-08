"""Bybit exchange scraper using official API."""

import asyncio
from typing import List
from datetime import datetime
from pybit.unified_trading import HTTP
from src.scrapers.base_scraper import BaseScraper
from src.models import PriceData
from src.config import settings


class BybitScraper(BaseScraper):
    """Scraper for Bybit exchange using official API."""
    
    def __init__(self):
        super().__init__("bybit")
        self.client = HTTP(
            testnet=False,
            api_key=settings.BYBIT_API_KEY,
            api_secret=settings.BYBIT_API_SECRET,
        )
    
    async def fetch_price(self, symbol: str) -> PriceData:
        """Fetch price for a single symbol from Bybit."""
        formatted_symbol = self.format_symbol(symbol)
        
        try:
            # Run synchronous API call in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_tickers(category="spot", symbol=formatted_symbol)
            )
            
            if response["retCode"] == 0 and response["result"]["list"]:
                ticker = response["result"]["list"][0]
                return PriceData(
                    exchange=self.exchange_name,
                    symbol=formatted_symbol,
                    price=float(ticker["lastPrice"]),
                    volume_24h=float(ticker["volume24h"]),
                    timestamp=datetime.utcnow()
                )
            else:
                raise ValueError(f"Failed to fetch {formatted_symbol} from Bybit: {response}")
        
        except Exception as e:
            print(f"Error fetching {formatted_symbol} from Bybit: {e}")
            raise
    
    async def fetch_all_prices(self, symbols: List[str]) -> List[PriceData]:
        """Fetch prices for multiple symbols from Bybit."""
        tasks = [self.fetch_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        prices = []
        for result in results:
            if isinstance(result, PriceData):
                prices.append(result)
            elif isinstance(result, Exception):
                print(f"Bybit error: {result}")
        
        return prices


# Test function
async def main():
    """Test Bybit scraper."""
    scraper = BybitScraper()
    symbols = ["BTC", "ETH"]
    
    print(f"Fetching prices from Bybit for: {symbols}")
    prices = await scraper.fetch_all_prices(symbols)
    
    for price in prices:
        print(f"{price.symbol}: ${price.price:,.2f} (Volume: ${price.volume_24h:,.0f})")


if __name__ == "__main__":
    asyncio.run(main())
