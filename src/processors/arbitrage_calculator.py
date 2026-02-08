"""Arbitrage opportunity calculator using pandas."""

import pandas as pd
from typing import List, Dict
from itertools import combinations
from src.models import PriceData, ArbitrageOpportunity
from src.config import settings


class ArbitrageCalculator:
    """Calculator for finding arbitrage opportunities across exchanges."""
    
    def __init__(self):
        self.settings = settings
    
    def calculate_opportunities(self, prices: List[PriceData]) -> List[ArbitrageOpportunity]:
        """
        Calculate arbitrage opportunities from price data.
        
        Args:
            prices: List of PriceData from multiple exchanges
        
        Returns:
            List of ArbitrageOpportunity objects
        """
        if not prices:
            return []
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame([
            {
                "exchange": p.exchange,
                "symbol": p.symbol,
                "price": p.price,
                "timestamp": p.timestamp
            }
            for p in prices
        ])
        
        opportunities = []
        
        # Group by symbol to compare prices across exchanges
        for symbol in df["symbol"].unique():
            symbol_df = df[df["symbol"] == symbol].copy()
            
            # Need at least 2 exchanges to compare
            if len(symbol_df) < 2:
                continue
            
            # Find all pairs of exchanges
            exchanges = symbol_df["exchange"].unique()
            for ex1, ex2 in combinations(exchanges, 2):
                price1 = symbol_df[symbol_df["exchange"] == ex1]["price"].values[0]
                price2 = symbol_df[symbol_df["exchange"] == ex2]["price"].values[0]
                
                # Determine buy and sell exchanges
                if price1 < price2:
                    buy_exchange, buy_price = ex1, price1
                    sell_exchange, sell_price = ex2, price2
                else:
                    buy_exchange, buy_price = ex2, price2
                    sell_exchange, sell_price = ex1, price1
                
                # Calculate price difference
                price_diff = sell_price - buy_price
                price_diff_pct = (price_diff / buy_price) * 100
                
                # Calculate estimated profit after fees
                buy_fee = self.settings.get_exchange_fee(buy_exchange)
                sell_fee = self.settings.get_exchange_fee(sell_exchange)
                total_fees = buy_fee + sell_fee
                #
                estimated_profit_pct = price_diff_pct - total_fees
                
                # Create opportunity
                opportunity = ArbitrageOpportunity(
                    symbol=symbol,
                    buy_exchange=buy_exchange,
                    sell_exchange=sell_exchange,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    price_diff=price_diff,
                    price_diff_pct=price_diff_pct,
                    estimated_profit_pct=estimated_profit_pct
                )
                
                opportunities.append(opportunity)
        
        # Sort by estimated profit descending
        opportunities.sort(key=lambda x: x.estimated_profit_pct, reverse=True)
        
        return opportunities
    
    def filter_profitable(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """
        Filter opportunities to only profitable ones above threshold.
        
        Args:
            opportunities: List of ArbitrageOpportunity objects
        
        Returns:
            Filtered list of profitable opportunities
        """
        return [
            opp for opp in opportunities
            if opp.estimated_profit_pct >= self.settings.MIN_PROFIT_THRESHOLD
        ]
    
    def get_summary_dataframe(self, opportunities: List[ArbitrageOpportunity]) -> pd.DataFrame:
        """
        Convert opportunities to pandas DataFrame for analysis.
        
        Args:
            opportunities: List of ArbitrageOpportunity objects
        
        Returns:
            DataFrame with opportunity details
        """
        if not opportunities:
            return pd.DataFrame()
        
        data = [
            {
                "Symbol": opp.symbol,
                "Buy From": opp.buy_exchange.upper(),
                "Buy Price": opp.buy_price,
                "Sell To": opp.sell_exchange.upper(),
                "Sell Price": opp.sell_price,
                "Price Diff %": round(opp.price_diff_pct, 2),
                "Est. Profit %": round(opp.estimated_profit_pct, 2),
                "Timestamp": opp.timestamp
            }
            for opp in opportunities
        ]
        
        return pd.DataFrame(data)


# Test function
if __name__ == "__main__":
    from datetime import datetime
    
    # Test data
    test_prices = [
        PriceData(exchange="binance", symbol="BTCUSDT", price=45000.0, timestamp=datetime.utcnow()),
        PriceData(exchange="bybit", symbol="BTCUSDT", price=45200.0, timestamp=datetime.utcnow()),
        PriceData(exchange="kucoin", symbol="BTCUSDT", price=44900.0, timestamp=datetime.utcnow()),
        PriceData(exchange="binance", symbol="ETHUSDT", price=2500.0, timestamp=datetime.utcnow()),
        PriceData(exchange="bybit", symbol="ETHUSDT", price=2520.0, timestamp=datetime.utcnow()),
    ]
    
    calculator = ArbitrageCalculator()
    opportunities = calculator.calculate_opportunities(test_prices)
    
    print(f"Found {len(opportunities)} opportunities:")
    for opp in opportunities:
        print(f"  {opp.symbol}: Buy {opp.buy_exchange} @ ${opp.buy_price}, "
              f"Sell {opp.sell_exchange} @ ${opp.sell_price}, "
              f"Profit: {opp.estimated_profit_pct:.2f}%")
    
    # Show DataFrame
    df = calculator.get_summary_dataframe(opportunities)
    print("\nDataFrame:")
    print(df)
