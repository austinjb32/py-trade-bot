"""
Database models for the trading bot.
This file contains the SQLAlchemy ORM models for storing trade data.
"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from db_config import Base

class Trade(Base):
    """Model for storing trade data"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    ticket = Column(BigInteger, unique=True, index=True)
    symbol = Column(String, index=True)
    type = Column(String)  # "BUY" or "SELL"
    volume = Column(Float)
    price_open = Column(Float)
    price_close = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    time_open = Column(DateTime, default=datetime.utcnow)
    time_close = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationship with signals
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    signal = relationship("Signal", back_populates="trades")


class Signal(Base):
    """Model for storing trade signals"""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    signal_type = Column(String)  # "BUY", "SELL", or "HOLD"
    confidence = Column(Float, nullable=True)
    reason = Column(String, nullable=True)
    time_generated = Column(DateTime, default=datetime.utcnow)
    executed = Column(Boolean, default=False)
    
    # Relationship with trades
    trades = relationship("Trade", back_populates="signal")


class DailyInvestment(Base):
    """Model for tracking daily investments"""
    __tablename__ = "daily_investments"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, index=True)
    amount = Column(Float, default=0.0)
    

class NewsEvent(Base):
    """Model for tracking news events"""
    __tablename__ = "news_events"

    id = Column(Integer, primary_key=True, index=True)
    event_time = Column(DateTime, index=True)
    event_name = Column(String)
    currency = Column(String, index=True)
    impact = Column(String)  # "HIGH", "MEDIUM", "LOW"
    actual = Column(String, nullable=True)
    forecast = Column(String, nullable=True)
    previous = Column(String, nullable=True)
    processed = Column(Boolean, default=False)


class MarketData(Base):
    """Model for storing market data snapshots"""
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    bid = Column(Float)
    ask = Column(Float)
    spread = Column(Float)
    time = Column(DateTime, index=True)
    
    # Additional price information
    bidhigh = Column(Float, nullable=True)
    bidlow = Column(Float, nullable=True)
    askhigh = Column(Float, nullable=True)
    asklow = Column(Float, nullable=True)
    
    # Account information
    balance = Column(Float, nullable=True)
    equity = Column(Float, nullable=True)
    margin = Column(Float, nullable=True)
    margin_free = Column(Float, nullable=True)
    margin_level = Column(Float, nullable=True)
    
    # Profit metrics
    daily_profit_target = Column(Float, nullable=True)
    current_daily_profit = Column(Float, nullable=True)
    profit_target_achieved = Column(Boolean, default=False)
    
    # Prediction (can be updated later)
    predicted_profit = Column(Float, nullable=True)
    predicted_direction = Column(String, nullable=True)  # "UP", "DOWN", "NEUTRAL"
