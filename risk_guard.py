# risk_guard.py

from together import Together
import config
import news_fetcher
import trade_executor
import MetaTrader5 as mt5

client = Together(api_key=config.TOGETHER_API_KEY)

def check_news_risk():
    """Check news for risk and handle trades accordingly.
    
    Returns:
        bool: True if high risk detected (trades should close), False otherwise.
    """
    try:
        latest_news = news_fetcher.get_latest_headlines()

        prompt = f"""
        Headlines:
        {latest_news}

        Based on these, should I CLOSE all EUR/USD trades now due to risk?
        Answer 'YES' if there is high risk or bad news, else 'NO'.
        """

        print(prompt)

        try:
            response = client.chat.completions.create(
                model=config.TOGETHER_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            # Don't print entire response object, only the content
            result = response.choices[0].message.content.strip().upper() if response.choices else ""
        except Exception as e:
            print(f"[RiskGuard] Error getting LLM response: {e}")
            # Default to not closing trades if API fails
            result = "NO"

        # Parse decision - check if YES appears in the first few words
        first_words = result.split()[:3]  # Check first 3 words
        decision = any("YES" in word for word in first_words)

        # Initialize MT5 with proper error handling
        try:
            if not mt5.initialize():
                print("[RiskGuard] MT5 failed to initialize!")
                # Still return decision even if MT5 fails
                return decision

            login_result = mt5.login(config.MT5_ACCOUNT, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
            if not login_result:
                print(f"[RiskGuard] MT5 login failed! Error code: {mt5.last_error()}")
                mt5.shutdown()
                return decision

            # Get positions with error handling
            positions = mt5.positions_get(symbol=config.SYMBOL)
            if positions is None:
                print(f"[RiskGuard] Failed to get positions. Error: {mt5.last_error()}")
                positions = []

            # Take action based on decision
            try:
                if decision:
                    print("[RiskGuard] High risk detected — closing all trades.")
                    if positions:
                        trade_executor.close_all_trades()
                elif not positions:
                    trade_executor.place_trade("BUY")
            except Exception as e:
                print(f"[RiskGuard] Error executing trade action: {e}")

            # Get updated positions after actions
            positions = mt5.positions_get(symbol=config.SYMBOL) or []
                
            # Gather trade stats
            stats = []
            for pos in positions:
                trade_info = {
                    'ticket': pos.ticket,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'profit': pos.profit,
                    'time': pos.time,
                }
                stats.append(trade_info)            
        except Exception as e:
            print(f"[RiskGuard] Error in MT5 operations: {e}")
        finally:
            # Always attempt to close MT5 session, even if there were errors
            try:
                mt5.shutdown()
            except Exception as e:
                print(f"[RiskGuard] Error closing MT5 session: {e}")

        # For bot.py compatibility, return boolean instead of dict
        return decision
        
    except Exception as e:
        print(f"[RiskGuard] Unhandled error in check_news_risk: {e}")
        return False  # Default to not closing trades on error

