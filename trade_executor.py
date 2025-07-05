# trade_executor.py

import MetaTrader5 as mt5
import config
from db_config import SessionLocal
import db_service

def get_allowed_filling_mode(symbol):
    """Get the first allowed filling mode for the specified symbol"""
    # Default filling mode if we can't determine the allowed ones
    default_mode = mt5.ORDER_FILLING_FOK  # Fill-or-Kill
    
    # Get the filling mode flags
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Error: Failed to get symbol info for {symbol}, using default filling mode")
        return default_mode
        
    filling_flags = symbol_info.filling_mode
    
    # Check available filling modes in order of preference
    if filling_flags & mt5.ORDER_FILLING_FOK:
        return mt5.ORDER_FILLING_FOK  # Fill-or-Kill
    elif filling_flags & mt5.ORDER_FILLING_IOC:
        return mt5.ORDER_FILLING_IOC  # Immediate-or-Cancel
    elif filling_flags & mt5.ORDER_FILLING_RETURN:
        return mt5.ORDER_FILLING_RETURN  # Return
    else:
        print(f"Warning: No recognized filling mode flags for {symbol}, using default")
        return default_mode

def connect_mt5():
    if not mt5.initialize():
        raise Exception("MT5 failed to initialize")
    authorized = mt5.login(config.MT5_ACCOUNT, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
    if not authorized:
        raise Exception("MT5 login failed")

def place_trade(signal, lot_size=None):
    # Use provided lot_size or default to config.BASE_LOT
    lot = lot_size if lot_size is not None else config.BASE_LOT
    symbol = config.SYMBOL
    if signal == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
    elif signal == "SELL":
        order_type = mt5.ORDER_TYPE_SELL
    else:
        return None
        
    # Get current price
    price = mt5.symbol_info_tick(symbol).ask if signal == "BUY" else mt5.symbol_info_tick(symbol).bid

    # Create a simplified market order request - don't specify filling mode at all
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 10,
        "magic": 234000,
        "comment": "DeepSeekBot",
        "type_time": mt5.ORDER_TIME_GTC,
    }
    result = mt5.order_send(request)
    return result

def close_all_trades():
    positions = mt5.positions_get(symbol=config.SYMBOL)
    
    for pos in positions:
        if pos.type == 0:  # BUY
            close_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(config.SYMBOL).bid
        else:  # SELL
            close_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(config.SYMBOL).ask
            
        # Simplified request without specifying filling mode
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
        }
        result = mt5.order_send(request)
        
        # Update the database with the closed trade
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            db = SessionLocal()
            try:
                # Update the trade in the database
                db_service.close_trade(db, pos.ticket, price, pos.profit)
            except Exception as e:
                print(f"Error updating database for closed trade: {e}")
            finally:
                db.close()
