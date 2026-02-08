
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import settings
from src.notifications.notifier import Notifier
from src.models import ArbitrageOpportunity

async def test_telegram_direct():
    print("--- Testing Telegram Notification ---")
    print(f"Token: {settings.TELEGRAM_BOT_TOKEN[:5]}...{settings.TELEGRAM_BOT_TOKEN[-5:] if settings.TELEGRAM_BOT_TOKEN else 'MISSING'}")
    print(f"Chat ID: {settings.TELEGRAM_CHAT_ID}")

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("ERROR: Credentials missing in settings.")
        return

    notifier = Notifier()
    
    # Create fake opportunity
    test_opp = ArbitrageOpportunity(
        symbol="TESTUSDT",
        buy_exchange="TestBybit",
        sell_exchange="TestBinance",
        buy_price=100.0,
        sell_price=101.0,
        price_diff=1.0,
        price_diff_pct=1.0,
        estimated_profit_pct=0.8
    )

    print("Sending test message...")
    try:
        await notifier.send_summary([test_opp])
        print("✅ SUCCESS: Message sent (check your Telegram!)")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram_direct())
