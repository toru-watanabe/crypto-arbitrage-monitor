"""Binance exchange scraper using public API."""

import aiohttp
from typing import List
from datetime import datetime
from src.scrapers.base_scraper import BaseScraper
from src.models import PriceData


class BinanceScraper(BaseScraper):
    """Scraper for Binance exchange using public REST API."""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    def __init__(self):
        super().__init__("binance")
    
    async def fetch_price(self, symbol: str) -> PriceData:
        """Fetch price for a single symbol from Binance."""
        formatted_symbol = self.format_symbol(symbol)
        
        async with aiohttp.ClientSession() as session:
            try:
                # Get ticker price
                url = f"{self.BASE_URL}/ticker/24hr"
                params = {"symbol": formatted_symbol}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return PriceData(
                            exchange=self.exchange_name,
                            symbol=formatted_symbol,
                            price=float(data["lastPrice"]),
                            volume_24h=float(data["volume"]) * float(data["weightedAvgPrice"]),
                            timestamp=datetime.utcnow()
                        )
                    else:
                        error_text = await response.text()
                        raise ValueError(f"Binance API error {response.status}: {error_text}")
            
            except Exception as e:
                print(f"Error fetching {formatted_symbol} from Binance: {e}")
                raise
    
    async def fetch_all_prices(self, symbols: List[str]) -> List[PriceData]:
        """Fetch prices for multiple symbols from Binance."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for symbol in symbols:
                formatted_symbol = self.format_symbol(symbol)
                url = f"{self.BASE_URL}/ticker/24hr"
                params = {"symbol": formatted_symbol}
                tasks.append(self._fetch_single(session, symbol, url, params))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            prices = []
            for result in results:
                if isinstance(result, PriceData):
                    prices.append(result)
                elif isinstance(result, Exception):
                    print(f"Binance error: {result}")
            
            return prices
    
    async def _fetch_single(self, session: aiohttp.ClientSession, symbol: str, url: str, params: dict) -> PriceData:
        """Helper method to fetch single price with existing session."""
        formatted_symbol = self.format_symbol(symbol)
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return PriceData(
                        exchange=self.exchange_name,
                        symbol=formatted_symbol,
                        price=float(data["lastPrice"]),
                        volume_24h=float(data["volume"]) * float(data["weightedAvgPrice"]),
                        timestamp=datetime.utcnow()
                    )
                else:
                    error_text = await response.text()
                    raise ValueError(f"Binance API error {response.status}: {error_text}")
        except Exception as e:
            print(f"Error fetching {formatted_symbol} from Binance: {e}")
            raise


# Test function
import asyncio

async def main():
    """Test Binance scraper."""
    scraper = BinanceScraper()
    symbols = ["BTC", "ETH"]
    
    print(f"Fetching prices from Binance for: {symbols}")
    prices = await scraper.fetch_all_prices(symbols)
    
    for price in prices:
        print(f"{price.symbol}: ${price.price:,.2f} (Volume: ${price.volume_24h:,.0f})")


if __name__ == "__main__":
    asyncio.run(main())
