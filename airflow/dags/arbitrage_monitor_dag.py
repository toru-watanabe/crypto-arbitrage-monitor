"""Airflow DAG for crypto arbitrage monitoring."""

import asyncio
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Import our components
import sys
sys.path.insert(0, '/app')

from src.config import settings
from src.scrapers import BybitScraper, BinanceScraper, KuCoinScraper
from src.storage import RedisClient, TimescaleClient
from src.processors import ArbitrageCalculator
from src.notifications import Notifier


def scrape_all_exchanges(**context):
    """Scrape prices from all exchanges and store in Redis."""
    print("Starting price scraping...")
    
    async def _scrape():
        # Initialize scrapers
        bybit = BybitScraper()
        binance = BinanceScraper()
        kucoin = KuCoinScraper()
        
        coins = settings.coin_list
        print(f"Scraping {len(coins)} coins: {coins}")
        
        # Fetch prices from all exchanges concurrently
        results = await asyncio.gather(
            bybit.fetch_all_prices(coins),
            binance.fetch_all_prices(coins),
            kucoin.fetch_all_prices(coins),
            return_exceptions=True
        )
        
        # Flatten results
        all_prices = []
        for result in results:
            if isinstance(result, list):
                all_prices.extend(result)
            elif isinstance(result, Exception):
                print(f"Scraping error: {result}")
        
        print(f"Successfully scraped {len(all_prices)} prices")
        
        # Store in Redis
        redis_client = RedisClient()
        redis_client.set_prices_batch(all_prices, ttl=300)
        print("Prices stored in Redis")
        
        # Push to XCom for next task
        return len(all_prices)
    
    # Run async function
    result = asyncio.run(_scrape())
    context['task_instance'].xcom_push(key='prices_count', value=result)


def calculate_arbitrage(**context):
    """Calculate arbitrage opportunities from cached prices."""
    print("Calculating arbitrage opportunities...")
    
    # Get prices from Redis
    redis_client = RedisClient()
    all_prices = redis_client.get_all_latest_prices()
    
    print(f"Loaded {len(all_prices)} prices from Redis")
    
    if not all_prices:
        print("No prices available for calculation")
        return 0
    
    # Calculate opportunities
    calculator = ArbitrageCalculator()
    opportunities = calculator.calculate_opportunities(all_prices)
    
    print(f"Found {len(opportunities)} total price differences")
    
    # Filter profitable opportunities
    profitable = calculator.filter_profitable(opportunities)
    print(f"Found {len(profitable)} profitable opportunities (>{settings.MIN_PROFIT_THRESHOLD}%)")
    
    # Store opportunities in XCom
    context['task_instance'].xcom_push(
        key='opportunities',
        value=[opp.model_dump() for opp in profitable]
    )
    
    return len(profitable)


def store_to_timescale(**context):
    """Store prices to TimescaleDB for long-term analysis."""
    print("Storing prices to TimescaleDB...")
    
    # Get prices from Redis
    redis_client = RedisClient()
    all_prices = redis_client.get_all_latest_prices()
    
    if not all_prices:
        print("No prices to store")
        return 0
    
    # Store in TimescaleDB
    timescale_client = TimescaleClient()
    timescale_client.insert_prices_batch(all_prices)
    
    print(f"Stored {len(all_prices)} prices to TimescaleDB")
    return len(all_prices)


def send_notifications(**context):
    """Send notifications for profitable opportunities."""
    print("Checking for notification triggers...")
    
    # Get opportunities from previous task
    ti = context['task_instance']
    opportunities_data = ti.xcom_pull(task_ids='calculate_arbitrage', key='opportunities')
    
    if not opportunities_data:
        print("No opportunities to notify")
        return 0
    
    # Convert back to ArbitrageOpportunity objects
    from src.models import ArbitrageOpportunity
    opportunities = [ArbitrageOpportunity(**opp_data) for opp_data in opportunities_data]
    
    print(f"Notifying {len(opportunities)} opportunities")
    
    async def _notify():
        notifier = Notifier()
        
        # Send individual notifications for high-value opportunities
        high_value = [opp for opp in opportunities if opp.estimated_profit_pct >= 1.0]
        if high_value:
            await notifier.notify_opportunities(high_value)
        
        # Send summary
        await notifier.send_summary(opportunities)
    
    # Run async notification
    asyncio.run(_notify())
    
    return len(opportunities)


# Define default arguments
default_args = {
    'owner': 'arbitrage-monitor',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=60),
}

# Define the DAG
dag = DAG(
    'crypto_arbitrage_monitor',
    default_args=default_args,
    description='Monitor cryptocurrency prices and find arbitrage opportunities',
    schedule=timedelta(seconds=settings.SCRAPE_INTERVAL),
    catchup=False,
    tags=['crypto', 'arbitrage', 'monitoring'],
)

# Define tasks
scrape_task = PythonOperator(
    task_id='scrape_prices',
    python_callable=scrape_all_exchanges,
    dag=dag,
)

calculate_task = PythonOperator(
    task_id='calculate_arbitrage',
    python_callable=calculate_arbitrage,
    dag=dag,
)

store_task = PythonOperator(
    task_id='store_historical',
    python_callable=store_to_timescale,
    dag=dag,
)

notify_task = PythonOperator(
    task_id='send_notifications',
    python_callable=send_notifications,
    dag=dag,
)

# Set task dependencies
scrape_task >> calculate_task >> [store_task, notify_task]
