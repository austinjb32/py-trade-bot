"""
Main trading bot module that coordinates all other components.
This module contains the main trading loop and orchestrates the trading process.
"""
import time
import traceback
import MetaTrader5 as mt5
import config
import risk_guard
import trade_executor
import db_service
from trade_manager import TradeManager
from market_data import MarketDataCollector

class TradingBot:
    def __init__(self):
        """Initialize the trading bot"""
        self.trade_manager = TradeManager()
        self.market_data = MarketDataCollector()
        # Initialize the database
        db_service.init_db()
    
    def setup(self):
        """Setup initial connections and configurations"""
        # Connect to MT5 terminal
        trade_executor.connect_mt5()
        
        # Check for daily investment limit in config
        if not hasattr(config, 'DAILY_INVESTMENT_LIMIT'):
            print("Warning: DAILY_INVESTMENT_LIMIT not set in config.py. Using default $20")
            config.DAILY_INVESTMENT_LIMIT = 20.0
    
    def run(self):
        """Run the main trading loop"""
        try:
            # Setup initial connections
            self.setup()
            
            # Main trading loop
            while True:
                try:
                    # Check for high-risk news events
                    high_risk = risk_guard.check_news_risk()
                    
                    if high_risk:
                        print("High risk detected - closing trades")
                        trade_executor.close_all_trades()
                    else:
                        # Process trades if no risk detected
                        self.trade_manager.process_trades()
                    
                    # Sleep interval between checks
                    print(f"Sleeping for {config.CHECK_INTERVAL_SECONDS} seconds...")
                    time.sleep(config.CHECK_INTERVAL_SECONDS)
                    
                except Exception as e:
                    print(f"Error in trading loop: {e}")
                    traceback.print_exc()
                    time.sleep(60)  # Wait a bit longer after an error
                    
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
        except Exception as e:
            print(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            # Clean up resources
            if mt5.terminal_info() is not None:
                mt5.shutdown()
                print("MT5 connection closed")