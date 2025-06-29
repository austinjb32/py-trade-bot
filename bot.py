# bot.py

import signal_engine, risk_guard, trade_executor, config
import MetaTrader5 as mt5
import time
from datetime import datetime, timedelta

trade_executor.connect_mt5()
next_news_check = datetime.now()

while True:
    if datetime.now() >= next_news_check:
        if risk_guard.check_news_risk():
            trade_executor.close_all_trades()
        next_news_check = datetime.now() + timedelta(minutes=30)

    signal = signal_engine.get_trade_signal()
    if signal in ["BUY", "SELL"]:
        trade_executor.place_trade(signal)

    time.sleep(60)  # Run loop every 1 min
