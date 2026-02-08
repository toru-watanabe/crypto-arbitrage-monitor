"""TimescaleDB client for long-term storage."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import settings
from src.models import PriceData

Base = declarative_base()


class PriceHistory(Base):
    """SQLAlchemy model for price history."""
    
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)


class TimescaleClient:
    """Client for interacting with TimescaleDB."""
    
    def __init__(self):
        self.engine = create_engine(settings.postgres_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def init_database(self):
        """Initialize database schema and create hypertable."""
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Convert to hypertable (TimescaleDB specific)
        with self.engine.connect() as conn:
            try:
                conn.execute(text(
                    "SELECT create_hypertable('price_history', 'timestamp', "
                    "if_not_exists => TRUE);"
                ))
                conn.commit()
                print("TimescaleDB hypertable created successfully")
            except Exception as e:
                print(f"Hypertable creation info: {e}")
    
    def insert_price(self, price_data: PriceData):
        """
        Insert a single price record.
        
        Args:
            price_data: PriceData object to store
        """
        session = self.Session()
        try:
            record = PriceHistory(
                exchange=price_data.exchange,
                symbol=price_data.symbol,
                price=price_data.price,
                volume_24h=price_data.volume_24h,
                timestamp=price_data.timestamp
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error inserting price: {e}")
            raise
        finally:
            session.close()
    
    def insert_prices_batch(self, prices: List[PriceData]):
        """
        Insert multiple price records in batch.
        
        Args:
            prices: List of PriceData objects
        """
        session = self.Session()
        try:
            records = [
                PriceHistory(
                    exchange=p.exchange,
                    symbol=p.symbol,
                    price=p.price,
                    volume_24h=p.volume_24h,
                    timestamp=p.timestamp
                )
                for p in prices
            ]
            session.bulk_save_objects(records)
            session.commit()
            print(f"Inserted {len(records)} price records")
        except Exception as e:
            session.rollback()
            print(f"Error inserting batch: {e}")
            raise
        finally:
            session.close()
    
    def get_latest_prices(self, symbol: str, limit: int = 100) -> List[dict]:
        """
        Get latest prices for a symbol across all exchanges.
        
        Args:
            symbol: Trading symbol
            limit: Maximum number of records per exchange
        
        Returns:
            List of price records as dictionaries
        """
        session = self.Session()
        try:
            query = text("""
                SELECT DISTINCT ON (exchange, symbol)
                    exchange, symbol, price, volume_24h, timestamp
                FROM price_history
                WHERE symbol = :symbol
                ORDER BY exchange, symbol, timestamp DESC
                LIMIT :limit
            """)
            
            result = session.execute(query, {"symbol": symbol, "limit": limit})
            return [dict(row._mapping) for row in result]
        finally:
            session.close()
    
    def get_price_history(
        self,
        symbol: str,
        exchange: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[dict]:
        """
        Get historical prices with optional filtering.
        
        Args:
            symbol: Trading symbol
            exchange: Optional exchange filter
            start_time: Optional start timestamp
            end_time: Optional end timestamp
            limit: Maximum number of records
        
        Returns:
            List of price records
        """
        session = self.Session()
        try:
            query = session.query(PriceHistory).filter(PriceHistory.symbol == symbol)
            
            if exchange:
                query = query.filter(PriceHistory.exchange == exchange)
            if start_time:
                query = query.filter(PriceHistory.timestamp >= start_time)
            if end_time:
                query = query.filter(PriceHistory.timestamp <= end_time)
            
            query = query.order_by(PriceHistory.timestamp.desc()).limit(limit)
            
            results = query.all()
            return [
                {
                    "exchange": r.exchange,
                    "symbol": r.symbol,
                    "price": r.price,
                    "volume_24h": r.volume_24h,
                    "timestamp": r.timestamp
                }
                for r in results
            ]
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"TimescaleDB health check failed: {e}")
            return False


# Test function
if __name__ == "__main__":
    client = TimescaleClient()
    
    # Health check
    print(f"TimescaleDB health: {client.health_check()}")
    
    # Initialize database
    client.init_database()
    print("Database initialized")
