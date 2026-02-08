"""Notification system for arbitrage opportunities."""

import asyncio
from typing import List
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from src.models import ArbitrageOpportunity
from src.config import settings


class Notifier:
    """Handles notifications for arbitrage opportunities."""
    
    def __init__(self):
        self.telegram_enabled = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)
        
        if self.telegram_enabled:
            self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            self.chat_id = settings.TELEGRAM_CHAT_ID
        else:
            print("⚠️ Telegram not configured. Notifications will only be logged.")
    
    async def send_telegram(self, message: str):
        """
        Send message via Telegram.
        
        Args:
            message: Message to send
        """
        if not self.telegram_enabled:
            print("Telegram not configured, skipping...")
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
            print(f"📱 Telegram notification sent successfully")
        except TelegramError as e:
            print(f"❌ Failed to send Telegram notification: {e}")
    
    def log_to_console(self, message: str):
        """Log notification to console."""
        print("\n" + "="*60)
        print(message)
        print("="*60 + "\n")
    
    def log_to_file(self, message: str, filename: str = "arbitrage_alerts.log"):
        """
        Log notification to file.
        
        Args:
            message: Message to log
            filename: Log file name
        """
        try:
            with open(filename, "a", encoding="utf-8") as f:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n[{timestamp}]\n{message}\n")
        except Exception as e:
            print(f"Failed to log to file: {e}")
    
    async def notify_opportunity(self, opportunity: ArbitrageOpportunity):
        """
        Send notification for a single arbitrage opportunity.
        
        Args:
            opportunity: ArbitrageOpportunity object
        """
        message = opportunity.to_message()
        
        # Log to console
        self.log_to_console(message)
        
        # Log to file
        self.log_to_file(message)
        
        # Send via Telegram if configured
        if self.telegram_enabled:
            await self.send_telegram(message)
    
    async def notify_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """
        Send notifications for multiple opportunities.
        
        Args:
            opportunities: List of ArbitrageOpportunity objects
        """
        if not opportunities:
            print("No opportunities to notify")
            return
        
        # Notify each opportunity
        for opp in opportunities:
            await self.notify_opportunity(opp)
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
    
    async def send_summary(self, opportunities: List[ArbitrageOpportunity]):
        """
        Send a summary of all opportunities.
        
        Args:
            opportunities: List of ArbitrageOpportunity objects
        """
        if not opportunities:
            message = "📊 No arbitrage opportunities found in this scan."
        else:
            message = f"📊 *Arbitrage Summary*\n\n"
            message += f"Found {len(opportunities)} opportunities:\n\n"
            
            for i, opp in enumerate(opportunities[:5], 1):  # Top 5
                message += (
                    f"{i}. *{opp.symbol}*: "
                    f"{opp.buy_exchange.upper()} → {opp.sell_exchange.upper()} "
                    f"({opp.estimated_profit_pct:+.2f}%)\n"
                )
            
            if len(opportunities) > 5:
                message += f"\n...and {len(opportunities) - 5} more"
        
        self.log_to_console(message)
        self.log_to_file(message)
        
        if self.telegram_enabled:
            await self.send_telegram(message)
    
    async def test_connection(self):
        """Test Telegram connection."""
        if not self.telegram_enabled:
            print("❌ Telegram not configured")
            return False
        
        try:
            me = await self.bot.get_me()
            print(f"✅ Telegram bot connected: @{me.username}")
            
            # Send test message
            test_msg = "🤖 *Crypto Arbitrage Monitor*\n\nBot successfully connected!"
            await self.send_telegram(test_msg)
            return True
        except TelegramError as e:
            print(f"❌ Telegram connection failed: {e}")
            return False


# Test function
async def main():
    """Test notifier."""
    notifier = Notifier()
    
    # Test connection
    if notifier.telegram_enabled:
        await notifier.test_connection()
    
    # Test notification
    from src.models import ArbitrageOpportunity
    from datetime import datetime
    
    test_opp = ArbitrageOpportunity(
        symbol="BTCUSDT",
        buy_exchange="kucoin",
        sell_exchange="bybit",
        buy_price=44900.0,
        sell_price=45200.0,
        price_diff=300.0,
        price_diff_pct=0.67,
        estimated_profit_pct=0.47,
        timestamp=datetime.utcnow()
    )
    
    await notifier.notify_opportunity(test_opp)


if __name__ == "__main__":
    asyncio.run(main())
