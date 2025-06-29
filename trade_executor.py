# trade_executor.py

import MetaTrader5 as mt5
import config

def connect_mt5():
    if not mt5.initialize():
        raise Exception("MT5 failed to initialize")
    authorized = mt5.login(config.MT5_ACCOUNT, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
    if not authorized:
        raise Exception("MT5 login failed")

def place_trade(signal):
    lot = config.BASE_LOT
    symbol = config.SYMBOL
    if signal == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
    elif signal == "SELL":
        order_type = mt5.ORDER_TYPE_SELL
    else:
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": mt5.symbol_info_tick(symbol).ask if signal == "BUY" else mt5.symbol_info_tick(symbol).bid,
        "deviation": 10,
        "magic": 234000,
        "comment": "DeepSeekBot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    print(f"Order sent: {result}")

def close_all_trades():
    positions = mt5.positions_get(symbol=config.SYMBOL)
    for pos in positions:
        if pos.type == 0:  # BUY
            close_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(config.SYMBOL).bid
        else:  # SELL
            close_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(config.SYMBOL).ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": config.SYMBOL,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 10,
            "magic": 234000,
            "comment": "CloseRiskGuard",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        mt5.order_send(request)
        print(f"Closed position: {pos.ticket}")
