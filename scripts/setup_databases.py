
import asyncio
import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import settings

def init_db():
    """Initialize TimescaleDB database and tables."""
    print("Connecting to TimescaleDB...")
    
    try:
        engine = create_engine(settings.postgres_url)
        
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            
            print("Creating price_history table...")
            # Match schema from src/storage/timescale_client.py
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id          SERIAL            PRIMARY KEY,
                    exchange    TEXT              NOT NULL,
                    symbol      TEXT              NOT NULL,
                    price       DOUBLE PRECISION  NOT NULL,
                    volume_24h  DOUBLE PRECISION  NULL,
                    timestamp   TIMESTAMPTZ       NOT NULL
                );
            """))
            
            print("Converting to hypertable...")
            # Ignore error if already a hypertable
            try:
                conn.execute(text("SELECT create_hypertable('price_history', 'timestamp', if_not_exists => TRUE);"))
            except Exception as e:
                print(f"Hypertable creation note: {e}")
                
            print("Creating indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_price_history_symbol ON price_history (symbol, timestamp DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_price_history_exchange ON price_history (exchange, timestamp DESC);"))
            
            print("Database initialization completed successfully!")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
