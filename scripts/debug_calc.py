
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage.redis_client import RedisClient
from src.processors.arbitrage_calculator import ArbitrageCalculator
from src.config import settings

def debug_arbitrage():
    print(f"--- Debugging Arbitrage Calculation ---")
    print(f"Config: Min Threshold={settings.MIN_PROFIT_THRESHOLD}%, Fees={settings.BYBIT_FEE}%")
    
    # 1. Fetch from Redis
    r = RedisClient()
    prices = r.get_all_latest_prices()
    print(f"Redis: Found {len(prices)} price records.")
    
    if not prices:
        print("ERROR: No prices in Redis! Scrapers might be failing.")
        return

    # Group by symbol to see coverage
    by_symbol = {}
    for p in prices:
        if p.symbol not in by_symbol: by_symbol[p.symbol] = []
        by_symbol[p.symbol].append(f"{p.exchange}: {p.price}")
    
    print("\n--- Price Snapshots ---")
    for s, data in by_symbol.items():
        print(f"{s}: {data}")

    # 2. Run Calculator
    calc = ArbitrageCalculator()
    opportunities = calc.calculate_opportunities(prices)
    print(f"\n--- Calculation Results ---")
    print(f"Total Raw Opportunities (Avg diff): {len(opportunities)}")
    
    for opp in opportunities:
        print(f"  > {opp.symbol} {opp.buy_exchange}->{opp.sell_exchange}: "
              f"Spread={opp.price_diff_pct:.4f}%, Profit={opp.estimated_profit_pct:.4f}% "
              f"(Buy: {opp.buy_price}, Sell: {opp.sell_price})")

    # 3. Filter
    profitable = calc.filter_profitable(opportunities)
    print(f"\n--- Profitable Opportunities (>{settings.MIN_PROFIT_THRESHOLD}%) ---")
    print(f"Count: {len(profitable)}")
    for p in profitable:
        print(f"  $$ {p.symbol}: Profit {p.estimated_profit_pct:.4f}%")

if __name__ == "__main__":
    debug_arbitrage()
