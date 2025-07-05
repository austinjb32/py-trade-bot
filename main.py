"""
Main entry point for the Forex trading bot.
This file has been refactored to use a modular approach with smaller files.
"""
from bot import TradingBot

def main():
    """Initialize and run the trading bot"""
    bot = TradingBot()
    bot.run()

if __name__ == "__main__":
    main()
