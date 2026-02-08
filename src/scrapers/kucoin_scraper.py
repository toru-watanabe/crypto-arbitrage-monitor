"""KuCoin exchange scraper using public API."""

import aiohttp
import asyncio
from typing import List
from datetime import datetime
from src.scrapers.base_scraper import BaseScraper
from src.models import PriceData


class KuCoinScraper(BaseScraper):
    """Scraper for KuCoin exchange using public REST API."""
    
    BASE_URL = "https://api.kucoin.com/api/v1"
    
    def __init__(self):
        super().__init__("kucoin")
    
    def format_symbol(self, symbol: str) -> str:
        """Format symbol for KuCoin (uses dash separator)."""
        return f"{symbol}-USDT"
    
    async def fetch_price(self, symbol: str) -> PriceData:
        """Fetch price for a single symbol from KuCoin."""
        formatted_symbol = self.format_symbol(symbol)
        
        async with aiohttp.ClientSession() as session:
            try:
                # Get ticker price
                url = f"{self.BASE_URL}/market/stats"
                params = {"symbol": formatted_symbol}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result["code"] == "200000" and result["data"]:
                            data = result["data"]
                            return PriceData(
                                exchange=self.exchange_name,
                                symbol=formatted_symbol,
                                price=float(data["last"]),
                                volume_24h=float(data["volValue"]) if data.get("volValue") else None,
                                timestamp=datetime.utcnow()
                            )
                        else:
                            raise ValueError(f"KuCoin API error: {result}")
                    else:
                        error_text = await response.text()
                        raise ValueError(f"KuCoin API error {response.status}: {error_text}")
            
            except Exception as e:
                print(f"Error fetching {formatted_symbol} from KuCoin: {e}")
                raise
    
    async def fetch_all_prices(self, symbols: List[str]) -> List[PriceData]:
        """Fetch prices for multiple symbols from KuCoin."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for symbol in symbols:
                formatted_symbol = self.format_symbol(symbol)
                url = f"{self.BASE_URL}/market/stats"
                params = {"symbol": formatted_symbol}
                tasks.append(self._fetch_single(session, symbol, url, params))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            prices = []
            for result in results:
                if isinstance(result, PriceData):
                    prices.append(result)
                elif isinstance(result, Exception):
                    print(f"KuCoin error: {result}")
            
            return prices
    
    async def _fetch_single(self, session: aiohttp.ClientSession, symbol: str, url: str, params: dict) -> PriceData:
        """Helper method to fetch single price with existing session."""
        formatted_symbol = self.format_symbol(symbol)
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result["code"] == "200000" and result["data"]:
                        data = result["data"]
                        return PriceData(
                            exchange=self.exchange_name,
                            symbol=f"{symbol}USDT",  # Normalize to match other exchanges
                            price=float(data["last"]),
                            volume_24h=float(data["volValue"]) if data.get("volValue") else None,
                            timestamp=datetime.utcnow()
                        )
                    else:
                        raise ValueError(f"KuCoin API error: {result}")
                else:
                    error_text = await response.text()
                    raise ValueError(f"KuCoin API error {response.status}: {error_text}")
        except Exception as e:
            print(f"Error fetching {formatted_symbol} from KuCoin: {e}")
            raise


# Test function
async def main():
    """Test KuCoin scraper."""
    scraper = KuCoinScraper()
    symbols = ["BTC", "ETH"]
    
    print(f"Fetching prices from KuCoin for: {symbols}")
    prices = await scraper.fetch_all_prices(symbols)
    
    for price in prices:
        print(f"{price.symbol}: ${price.price:,.2f} (Volume: ${price.volume_24h:,.0f})")


if __name__ == "__main__":
    asyncio.run(main())
