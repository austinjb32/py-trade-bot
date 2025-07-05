"""
Database service for the trading bot.
This file contains functions for interacting with the database.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
import models
from db_config import SessionLocal, engine, Base

# Create tables if they don't exist
def init_db():
    Base.metadata.create_all(bind=engine)

# Trade operations
def create_trade(db: Session, trade_data: dict):
    """Create a new trade record in the database"""
    db_trade = models.Trade(
        ticket=trade_data["ticket"],
        symbol=trade_data["symbol"],
        type=trade_data["type"],
        volume=trade_data["volume"],
        price_open=trade_data["price_open"],
        profit=trade_data.get("profit", 0.0),
        time_open=datetime.fromtimestamp(trade_data["time"]) if "time" in trade_data else datetime.utcnow(),
        is_active=True,
        signal_id=trade_data.get("signal_id")
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

def update_trade(db: Session, ticket: int, trade_data: dict):
    """Update an existing trade record"""
    db_trade = get_trade_by_ticket(db, ticket)
    if db_trade:
        for key, value in trade_data.items():
            if hasattr(db_trade, key):
                setattr(db_trade, key, value)
        db.commit()
        db.refresh(db_trade)
    return db_trade

def close_trade(db: Session, ticket: int, price_close: float, profit: float):
    """Mark a trade as closed with final price and profit"""
    db_trade = get_trade_by_ticket(db, ticket)
    if db_trade:
        db_trade.price_close = price_close
        db_trade.profit = profit
        db_trade.time_close = datetime.utcnow()
        db_trade.is_active = False
        db.commit()
        db.refresh(db_trade)
    return db_trade

def get_trade_by_ticket(db: Session, ticket: int):
    """Get a trade by its ticket number"""
    return db.query(models.Trade).filter(models.Trade.ticket == ticket).first()

def get_active_trades(db: Session, symbol: str = None):
    """Get all active trades, optionally filtered by symbol"""
    query = db.query(models.Trade).filter(models.Trade.is_active == True)
    if symbol:
        query = query.filter(models.Trade.symbol == symbol)
    return query.all()

# Signal operations
def create_signal(db: Session, signal_data: dict):
    """Create a new signal record in the database"""
    db_signal = models.Signal(
        symbol=signal_data["symbol"],
        signal_type=signal_data["signal_type"],
        confidence=signal_data.get("confidence"),
        reason=signal_data.get("reason"),
        executed=signal_data.get("executed", False)
    )
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)
    return db_signal

def update_signal_executed(db: Session, signal_id: int, executed: bool = True):
    """Mark a signal as executed"""
    db_signal = db.query(models.Signal).filter(models.Signal.id == signal_id).first()
    if db_signal:
        db_signal.executed = executed
        db.commit()
        db.refresh(db_signal)
    return db_signal

# Daily investment operations
def get_daily_investment(db: Session, date_obj: date):
    """Get the daily investment amount for a specific date"""
    date_start = datetime.combine(date_obj, datetime.min.time())
    db_investment = db.query(models.DailyInvestment).filter(
        models.DailyInvestment.date == date_start
    ).first()
    return db_investment.amount if db_investment else 0.0

def update_daily_investment(db: Session, date_obj: date, amount: float):
    """Update or create the daily investment amount for a specific date"""
    date_start = datetime.combine(date_obj, datetime.min.time())
    db_investment = db.query(models.DailyInvestment).filter(
        models.DailyInvestment.date == date_start
    ).first()
    
    if db_investment:
        db_investment.amount += amount
    else:
        db_investment = models.DailyInvestment(date=date_start, amount=amount)
        db.add(db_investment)
    
    db.commit()
    if db_investment:
        db.refresh(db_investment)
    return db_investment

# News event operations
def create_news_event(db: Session, news_data: dict):
    """Create a new news event record in the database"""
    db_news = models.NewsEvent(
        event_time=news_data["event_time"],
        event_name=news_data["event_name"],
        currency=news_data["currency"],
        impact=news_data["impact"],
        actual=news_data.get("actual"),
        forecast=news_data.get("forecast"),
        previous=news_data.get("previous"),
        processed=news_data.get("processed", False)
    )
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news

def get_upcoming_news_events(db: Session, hours: int = 24):
    """Get upcoming news events within the next specified hours"""
    now = datetime.utcnow()
    future = now + datetime.timedelta(hours=hours)
    return db.query(models.NewsEvent).filter(
        models.NewsEvent.event_time > now,
        models.NewsEvent.event_time < future
    ).all()
