"""
Trade manager module for executing trades and managing trade operations.
This module coordinates trade execution and signal processing.
"""
import time
import datetime
import config
import trade_executor
import signal_engine
from data_manager import DataManager
from market_data import MarketDataCollector

class TradeManager:
    def __init__(self):
        """Initialize the trade manager"""
        self.data_manager = DataManager()
        self.market_data = MarketDataCollector()
    
    def check_daily_limit(self):
        """Check if daily investment limit has been reached"""
        today = datetime.date.today()
        daily_invested = self.data_manager.get_daily_investment(today)
        
        if daily_invested >= config.DAILY_INVESTMENT_LIMIT:
            return True, 0.0
        
        remaining_budget = config.DAILY_INVESTMENT_LIMIT - daily_invested
        return False, remaining_budget
    
    def process_trades(self):
        """Process trades and return True if high risk is detected"""
        # Get current positions from MT5
        current_trades = self.market_data.get_positions_as_dict()
        
        # Get current market data
        symbol_info = self.market_data.get_symbol_info()
        # symbol_info now includes: symbol, bid, ask, bidhigh, bidlow, askhigh, asklow, spread, points, digits, trade_contract_size, time, currency_base, currency_profit, balance, equity, margin, margin_free, margin_level
        # symbol_info now includes: symbol, bid, ask, bidhigh, bidlow, askhigh, asklow, spread, points, digits, trade_contract_size, time, currency_base, currency_profit, balance, equity, margin, margin_free, margin_level
        
        # Get trading signal
        signal = signal_engine.get_trade_signal(current_trades, {
            "symbol": symbol_info["symbol"],
            "bid": symbol_info["bid"],
            "ask": symbol_info["ask"],
            "bidhigh": symbol_info["bidhigh"],
            "bidlow": symbol_info["bidlow"],
            "askhigh": symbol_info["askhigh"],
            "asklow": symbol_info["asklow"],
            "spread": symbol_info["spread"],
            "points": symbol_info["points"],
            "digits": symbol_info["digits"],
            "trade_contract_size": symbol_info["trade_contract_size"],
            "time": symbol_info["time"],
            "currency_base": symbol_info["currency_base"],
            "currency_profit": symbol_info["currency_profit"],
            "balance": symbol_info["balance"],
            "equity": symbol_info["equity"],
            "margin": symbol_info["margin"],
            "margin_free": symbol_info["margin_free"],
            "margin_level": symbol_info["margin_level"]
        })
        
        # Store signal in database
        signal_id = self.data_manager.create_signal(
            config.SYMBOL, 
            signal, 
            confidence=None,  # Could be added in future versions
            reason=None  # Could be added in future versions
        )
        
        # If signal is to buy or sell, execute the trade
        if signal in ["BUY", "SELL"]:
            # Check if we're within daily investment limit
            limit_reached, remaining_budget = self.check_daily_limit()
            if limit_reached:
                return False
                
            # Get currency price for lot calculation
            currency_price = self.market_data.get_currency_price()
            
            # Calculate lot size based on remaining budget
            lot_size = min(config.BASE_LOT, remaining_budget / (currency_price * 1000))
                        
            # Execute the trade
            trade_result = trade_executor.place_trade(signal, lot_size)
            
            # Update daily investment tracker
            today = datetime.date.today()
            self.data_manager.update_daily_investment(today, lot_size * currency_price * 1000)
            
            # Mark signal as executed
            self.data_manager.update_signal_executed(signal_id, True)
            
            # If trade was executed successfully, store it in database
            if trade_result and hasattr(trade_result, "order"):
                trade_data = {
                    "ticket": trade_result.order,
                    "symbol": config.SYMBOL,
                    "type": signal,
                    "volume": lot_size,
                    "price_open": trade_result.price,
                    "profit": 0.0,  # Initial profit is 0
                    "time": int(time.time()),
                    "signal_id": signal_id
                }
                self.data_manager.create_trade(trade_data)
            
            return False
        else:
            return False