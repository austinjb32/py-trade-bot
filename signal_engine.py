# signal_engine.py

from together import Together
import config

# Initialize Together client
client = Together(api_key=config.TOGETHER_API_KEY)

def get_trade_signal(current_trades=None, symbol_info=None):
    """
    Get trading signal from LLM based on current market conditions and open trades.
    
    Args:
        current_trades (list): List of dictionaries containing open trade information
        symbol_info (dict): Current symbol price and other market information
        
    Returns:
        str: Trading decision (BUY, SELL, or NO TRADE)
    """
    # Build detailed prompt with current trades and market data
    if current_trades is None:
        current_trades = []
        
    # Format open trades information
    trades_info = "\nCurrent Open Positions:\n"
    if current_trades:
        for trade in current_trades:
            trades_info += f"- Type: {trade['type']}, Volume: {trade['volume']}, Open Price: {trade['price_open']}, Current Profit: ${trade['profit']:.2f}\n"
    else:
        trades_info += "No open positions\n"
    
    # Format market data
    market_data = "\nCurrent Market Data:\n"
    if symbol_info:
        # Symbol and price info
        market_data += f"- Symbol: {symbol_info.get('symbol', 'N/A')}\n"
        market_data += f"- Bid: {symbol_info.get('bid', 'N/A')}\n"
        market_data += f"- Ask: {symbol_info.get('ask', 'N/A')}\n"
        market_data += f"- Bid High: {symbol_info.get('bidhigh', 'N/A')}\n"
        market_data += f"- Bid Low: {symbol_info.get('bidlow', 'N/A')}\n"
        market_data += f"- Ask High: {symbol_info.get('askhigh', 'N/A')}\n"
        market_data += f"- Ask Low: {symbol_info.get('asklow', 'N/A')}\n"
        market_data += f"- Spread: {symbol_info.get('spread', 'N/A')}\n"
        market_data += f"- Points: {symbol_info.get('points', 'N/A')}\n"
        market_data += f"- Digits: {symbol_info.get('digits', 'N/A')}\n"
        market_data += f"- Trade Contract Size: {symbol_info.get('trade_contract_size', 'N/A')}\n"
        market_data += f"- Time: {symbol_info.get('time', 'N/A')}\n"
        market_data += f"- Currency Base: {symbol_info.get('currency_base', 'N/A')}\n"
        market_data += f"- Currency Profit: {symbol_info.get('currency_profit', 'N/A')}\n"
        # Account info
        market_data += f"- Balance: ${symbol_info.get('balance', 'N/A')}\n"
        market_data += f"- Equity: ${symbol_info.get('equity', 'N/A')}\n"
        market_data += f"- Margin: ${symbol_info.get('margin', 'N/A')}\n"
        market_data += f"- Free Margin: ${symbol_info.get('margin_free', 'N/A')}\n"
        market_data += f"- Margin Level: {symbol_info.get('margin_level', 'N/A')}\n"
        market_data += f"- Trade Contract Size: {symbol_info.get('trade_contract_size', 'N/A')}\n"
        market_data += f"- Time: {symbol_info.get('time', 'N/A')}\n"
        market_data += f"- Currency Base: {symbol_info.get('currency_base', 'N/A')}\n"
        market_data += f"- Currency Profit: {symbol_info.get('currency_profit', 'N/A')}\n"
        
        # Account statistics (no separate account_stats dict)
        market_data += f"\nAccount Data:\n"
        market_data += f"- Balance: ${symbol_info.get('balance', 'N/A')}\n"
        market_data += f"- Equity: ${symbol_info.get('equity', 'N/A')}\n"
        market_data += f"- Free Margin: ${symbol_info.get('margin_free', 'N/A')}\n"
        
        # Profit target strategy
        market_data += f"\nProfit Target Strategy:\n"
        market_data += f"- Daily Profit Target: ${symbol_info.get('daily_profit_target', 'N/A')}\n"
        market_data += f"- Current Daily Profit: ${symbol_info.get('current_daily_profit', 'N/A')}\n"
        target_achieved = symbol_info.get('profit_target_achieved', False)
        market_data += f"- Target Status: {'ACHIEVED' if target_achieved else 'NOT YET ACHIEVED'}\n"
    else:
        market_data += "Market data not available\n"
    
    # Create the prompt
    prompt = f"""Based on the following information, should I BUY or SELL EUR/USD now?
{trades_info}
{market_data}

Please analyze the data and respond with only one of these options: 'BUY', 'SELL', or 'NO TRADE'.
If I already have positions open in the direction you recommend, consider if adding more is wise."""
        
    # Send to LLM with system prompt from config
    messages = [
        {"role": "system", "content": config.SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    response = client.chat.completions.create(
        model=config.TOGETHER_MODEL,
        messages=messages
    )
    
    result = response.choices[0].message.content.upper()
    
    # Extract the decision
    if "BUY" in result:
        return "BUY"
    elif "SELL" in result:
        return "SELL"
    else:
        return "NO TRADE"
