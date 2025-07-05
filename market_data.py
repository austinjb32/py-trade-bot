"""
Market data module for interacting with MetaTrader 5.
This module handles fetching market data and positions from MT5.
"""
import MetaTrader5 as mt5
import config
from db_config import SessionLocal
import db_service
from models import MarketData
import pytz
from datetime import datetime, date, timedelta

class MarketDataCollector:
    def __init__(self):
        """Initialize the market data collector"""
        pass
    
    def connect_mt5(self):
        """Connect to MT5 terminal"""
        if not mt5.initialize():
            raise Exception(f"MT5 initialization failed! Error code: {mt5.last_error()}")
        
        login_result = mt5.login(config.MT5_ACCOUNT, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
        if not login_result:
            raise Exception(f"MT5 login failed! Error code: {mt5.last_error()}")
        
        return True
    
    def disconnect_mt5(self):
        """Disconnect from MT5 terminal"""
        mt5.shutdown()
    
    def get_positions(self, symbol=None):
        """Get all current open positions, optionally filtered by symbol"""
        symbol_filter = symbol or config.SYMBOL
        try:
            self.connect_mt5()
            positions = mt5.positions_get(symbol=symbol_filter) or []
            return positions
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
        finally:
            self.disconnect_mt5()
    
    def get_positions_as_dict(self, symbol=None):
        """Get all current open positions as a list of dictionaries"""
        positions = self.get_positions(symbol)
        current_trades = []
        
        for pos in positions:
            trade_info = {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'BUY' if pos.type == 0 else 'SELL',
                'volume': pos.volume,
                'price_open': pos.price_open,
                'profit': pos.profit,
                'time': pos.time,
            }
            current_trades.append(trade_info)
            
            # Update trade in database if it exists
            db = SessionLocal()
            try:
                existing_trade = db_service.get_trade_by_ticket(db, pos.ticket)
                if existing_trade:
                    # Update profit information
                    db_service.update_trade(db, pos.ticket, {"profit": pos.profit})
                else:
                    # This is a new trade from MT5, store it in the database
                    db_service.create_trade(db, trade_info)
            except Exception as e:
                print(f"Error updating trade in database: {e}")
            finally:
                db.close()
        
        return current_trades
    
    def get_symbol_info(self, symbol=None):
        """Get symbol information from MT5 and calculate profit metrics"""
        symbol_name = symbol or config.SYMBOL
        try:
            self.connect_mt5()
            symbol_info_raw = mt5.symbol_info(symbol_name)
            if not symbol_info_raw:
                return {}
                
            # Convert to a regular dictionary
            symbol_info = {
                'symbol': symbol_name,
                'bid': symbol_info_raw.bid,
                'ask': symbol_info_raw.ask,
                'bidhigh': symbol_info_raw.bidhigh,
                'bidlow': symbol_info_raw.bidlow,
                'askhigh': symbol_info_raw.askhigh,
                'asklow': symbol_info_raw.asklow,
                'spread': symbol_info_raw.spread,
                'points': symbol_info_raw.point,
                'digits': symbol_info_raw.digits,
                'trade_contract_size': symbol_info_raw.trade_contract_size,
                'time': symbol_info_raw.time,
                'currency_base': symbol_info_raw.currency_base,
                'currency_profit': symbol_info_raw.currency_profit,
            }
            
            # Get additional account info
            account_info = mt5.account_info()
            if account_info:
                symbol_info['balance'] = account_info.balance
                symbol_info['equity'] = account_info.equity
                symbol_info['margin'] = account_info.margin
                symbol_info['margin_free'] = account_info.margin_free
                symbol_info['margin_level'] = account_info.margin_level
            
            # Calculate daily profit metrics - always populate with actual values, not None
            symbol_info['daily_profit_target'] = float(config.DAILY_PROFIT_TARGET)  # Ensure it's a float
            
            # Get today's profit from open and closed trades
            db = SessionLocal()
            try:
                # Get IST timezone
                ist_tz = pytz.timezone(config.TIMEZONE)
                today_ist = datetime.now(ist_tz).date()
                
                # Convert to UTC for database query (assuming DB stores in UTC)
                today_utc_start = datetime.combine(today_ist, datetime.min.time()).astimezone(pytz.UTC)
                today_utc_end = datetime.combine(today_ist, datetime.max.time()).astimezone(pytz.UTC)
                
                try:
                    # Query for today's profit from completed trades
                    closed_profit = db.query(db_service.func.sum(db_service.models.Trade.profit)).filter(
                        db_service.models.Trade.time_close.between(today_utc_start, today_utc_end)
                    ).scalar() or 0.0
                except Exception as e:
                    print(f"Error getting closed profit: {e}")
                    closed_profit = 0.0
                
                # Get profit from current open trades
                try:
                    positions = self.get_positions(symbol_name)
                    open_profit = sum(pos.profit for pos in positions) if positions else 0.0
                except Exception as e:
                    print(f"Error getting open positions profit: {e}")
                    open_profit = 0.0
                
                # Total daily profit - ensure we have a numeric value
                current_daily_profit = closed_profit + open_profit
                symbol_info['current_daily_profit'] = current_daily_profit
                print(f"[MarketData] Current daily profit: ${current_daily_profit:.2f}, Target: ${float(config.DAILY_PROFIT_TARGET):.2f}")
                
                # Check if target is achieved
                target_achieved = current_daily_profit >= float(config.DAILY_PROFIT_TARGET)
                symbol_info['profit_target_achieved'] = target_achieved
                
                # Simple prediction based on current trajectory
                if len(positions) > 0:
                    avg_hourly_profit = current_daily_profit / (datetime.now(ist_tz).hour + 1)  # avoid div by zero
                    hours_left = 24 - datetime.now(ist_tz).hour
                    predicted_profit = current_daily_profit + (avg_hourly_profit * hours_left * 0.7)  # conservative estimate
                    symbol_info['predicted_profit'] = predicted_profit
                    symbol_info['predicted_direction'] = 'UP' if open_profit > 0 else 'DOWN' if open_profit < 0 else 'NEUTRAL'
                
                # Save market data snapshot to database
                self.save_market_data_snapshot(symbol_info)
                
            except Exception as e:
                print(f"Error calculating profit metrics: {e}")
            finally:
                db.close()
                
            return symbol_info
        except Exception as e:
            print(f"Error getting symbol info: {e}")
            return {}
        finally:
            self.disconnect_mt5()
    
    def save_market_data_snapshot(self, symbol_info):
        """Save market data snapshot to the database with IST timezone timestamp"""
        try:
            # Get current time in IST
            ist_tz = pytz.timezone(config.TIMEZONE)
            current_time_ist = datetime.now(ist_tz)
            
            db = SessionLocal()
            try:
                # Create new market data snapshot
                market_data = MarketData(
                    symbol=symbol_info.get('symbol'),
                    bid=symbol_info.get('bid'),
                    ask=symbol_info.get('ask'),
                    spread=symbol_info.get('spread'),
                    time=current_time_ist,
                    
                    # Additional price info
                    bidhigh=symbol_info.get('bidhigh'),
                    bidlow=symbol_info.get('bidlow'),
                    askhigh=symbol_info.get('askhigh'),
                    asklow=symbol_info.get('asklow'),
                    
                    # Account information
                    balance=symbol_info.get('balance'),
                    equity=symbol_info.get('equity'),
                    margin=symbol_info.get('margin'),
                    margin_free=symbol_info.get('margin_free'),
                    margin_level=symbol_info.get('margin_level'),
                    
                    # Profit metrics
                    daily_profit_target=symbol_info.get('daily_profit_target'),
                    current_daily_profit=symbol_info.get('current_daily_profit'),
                    profit_target_achieved=symbol_info.get('profit_target_achieved', False),
                    
                    # Predictions
                    predicted_profit=symbol_info.get('predicted_profit'),
                    predicted_direction=symbol_info.get('predicted_direction')
                )
                
                db.add(market_data)
                db.commit()                
            except Exception as e:
                db.rollback()
                print(f"Error saving market data snapshot: {e}")
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error in save_market_data_snapshot: {e}")
    
    def get_currency_price(self, symbol=None):
        """Get current price for a currency pair"""
        symbol_name = symbol or config.SYMBOL
        symbol_info = self.get_symbol_info(symbol_name)
        if not symbol_info:
            # Default to 1.0 as fallback
            return 1.0
        # Use updated keys for bid and ask
        return (symbol_info.get('bid', 0) + symbol_info.get('ask', 0)) / 2