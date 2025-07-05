from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models to register them with SQLAlchemy
from app.models import Base, Asset, Portfolio, PortfolioHolding, Transaction, PriceData
from app.models.asset import AssetType


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with tables and sample data."""
    create_tables()
    
    # Add sample data if needed
    db = SessionLocal()
    try:
        # Check if we have any assets, if not, add some sample ones
        if not db.query(Asset).first():
            sample_assets = [
                Asset(
                    symbol="AAPL",
                    name="Apple Inc.",
                    asset_type=AssetType.STOCK,
                    sector="Technology",
                    industry="Consumer Electronics",
                    description="Designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
                ),
                Asset(
                    symbol="GOOGL",
                    name="Alphabet Inc.",
                    asset_type=AssetType.STOCK,
                    sector="Technology",
                    industry="Internet Software & Services",
                    description="Provides internet-based products and services worldwide."
                ),
                Asset(
                    symbol="MSFT",
                    name="Microsoft Corporation",
                    asset_type=AssetType.STOCK,
                    sector="Technology",
                    industry="Software & Services",
                    description="Develops, licenses, and supports software, services, devices, and solutions worldwide."
                ),
                Asset(
                    symbol="TSLA",
                    name="Tesla, Inc.",
                    asset_type=AssetType.STOCK,
                    sector="Consumer Discretionary",
                    industry="Automotive",
                    description="Designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems."
                ),
                Asset(
                    symbol="SPY",
                    name="SPDR S&P 500 ETF Trust",
                    asset_type=AssetType.ETF,
                    sector="Diversified",
                    industry="Exchange Traded Fund",
                    description="Seeks to provide investment results that correspond generally to the price and yield performance of the S&P 500 Index."
                ),
            ]
            
            for asset in sample_assets:
                db.add(asset)
            
            db.commit()
            print("Sample assets added to database")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
