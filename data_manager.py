"""
Data manager module for handling database operations related to trading.
This module provides a clean interface for daily investment tracking and
other database interactions.
"""
import datetime
import db_service
from db_config import SessionLocal

class DataManager:
    def __init__(self):
        """Initialize the data manager"""
        pass
    
    def get_daily_investment(self, date):
        """Get total amount invested on given date from database"""
        db = SessionLocal()
        try:
            return db_service.get_daily_investment(db, date)
        finally:
            db.close()
    
    def update_daily_investment(self, date, amount):
        """Add investment amount to daily tracker in database"""
        db = SessionLocal()
        try:
            investment = db_service.update_daily_investment(db, date, amount)
            return investment.amount
        finally:
            db.close()
    
    def create_signal(self, symbol, signal_type, confidence=None, reason=None):
        """Create a new signal record in the database"""
        db = SessionLocal()
        try:
            signal_data = {
                "symbol": symbol,
                "signal_type": signal_type,
                "confidence": confidence,
                "reason": reason
            }
            db_signal = db_service.create_signal(db, signal_data)
            return db_signal.id
        finally:
            db.close()
    
    def update_signal_executed(self, signal_id, executed=True):
        """Mark a signal as executed"""
        db = SessionLocal()
        try:
            db_service.update_signal_executed(db, signal_id, executed)
        finally:
            db.close()
    
    def create_trade(self, trade_data):
        """Create a new trade record in the database"""
        db = SessionLocal()
        try:
            db_trade = db_service.create_trade(db, trade_data)
            return db_trade.id
        finally:
            db.close()
    
    def update_trade(self, ticket, trade_data):
        """Update an existing trade record"""
        db = SessionLocal()
        try:
            db_service.update_trade(db, ticket, trade_data)
        finally:
            db.close()
    
    def get_active_trades(self, symbol=None):
        """Get all active trades, optionally filtered by symbol"""
        db = SessionLocal()
        try:
            return db_service.get_active_trades(db, symbol)
        finally:
            db.close()
