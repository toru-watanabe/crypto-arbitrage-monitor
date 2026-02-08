"""Data models for the arbitrage monitoring system."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PriceData(BaseModel):
    """Price data from an exchange."""
    
    exchange: str = Field(..., description="Exchange name (bybit, binance, kucoin)")
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    price: float = Field(..., description="Current price")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of price")
    volume_24h: Optional[float] = Field(None, description="24-hour trading volume")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ArbitrageOpportunity(BaseModel):
    """Detected arbitrage opportunity."""
    
    symbol: str = Field(..., description="Trading symbol")
    buy_exchange: str = Field(..., description="Exchange to buy from (lower price)")
    sell_exchange: str = Field(..., description="Exchange to sell on (higher price)")
    buy_price: float = Field(..., description="Price to buy at")
    sell_price: float = Field(..., description="Price to sell at")
    price_diff: float = Field(..., description="Absolute price difference")
    price_diff_pct: float = Field(..., description="Price difference percentage")
    estimated_profit_pct: float = Field(..., description="Estimated profit after fees")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_profitable(self) -> bool:
        """Check if this opportunity is profitable after fees."""
        return self.estimated_profit_pct > 0
    
    def to_message(self) -> str:
        """Generate notification message."""
        emoji = "🚀" if self.estimated_profit_pct > 1.0 else "💰"
        return (
            f"{emoji} *Arbitrage Opportunity Detected!*\n\n"
            f"Coin: *{self.symbol}*\n"
            f"Buy: {self.buy_exchange.upper()} at ${self.buy_price:,.2f}\n"
            f"Sell: {self.sell_exchange.upper()} at ${self.sell_price:,.2f}\n"
            f"Price Difference: {self.price_diff_pct:.2f}%\n"
            f"*Estimated Profit: {self.estimated_profit_pct:.2f}%*\n"
            f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
