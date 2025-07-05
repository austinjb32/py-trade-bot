"""
Streamlit UI for the Forex Trading Bot
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import threading
from db_config import SessionLocal
from models import Trade, Signal, DailyInvestment
from pages.Settings import load_settings
import risk_guard
import config
import trade_executor
from bot import TradingBot

# Page configuration
st.set_page_config(
    page_title="Forex Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global variables
bot_instance = None
bot_thread = None
stop_bot = threading.Event()

# Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
    }
    .stat-box {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        text-align: center;
    }
    .profit-positive {
        color: #4CAF50;
        font-weight: bold;
    }
    .profit-negative {
        color: #F44336;
        font-weight: bold;
    }
    .info-text {
        font-size: 0.9rem;
        color: #616161;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)  # Cache data for 10 seconds
def load_trade_data():
    """Load trade data from the database"""
    db = SessionLocal()
    try:
        # Get all trades
        trades = db.query(Trade).all()
        # Convert to DataFrame
        if trades:
            data = [{
                "id": t.id,
                "ticket": t.ticket,
                "symbol": t.symbol,
                "type": t.type,
                "volume": t.volume,
                "price_open": t.price_open,
                "price_close": t.price_close,
                "profit": t.profit,
                "time_open": t.time_open,
                "time_close": t.time_close,
                "is_active": t.is_active
            } for t in trades]
            return pd.DataFrame(data)
        return pd.DataFrame()
    finally:
        db.close()

@st.cache_data(ttl=10)
def load_signal_data():
    """Load signal data from the database"""
    db = SessionLocal()
    try:
        # Get all signals
        signals = db.query(Signal).all()
        # Convert to DataFrame
        if signals:
            data = [{
                "id": s.id,
                "symbol": s.symbol,
                "signal_type": s.signal_type,
                "confidence": s.confidence,
                "reason": s.reason,
                "timestamp": s.time_generated,
                "executed": s.executed
            } for s in signals]
            return pd.DataFrame(data)
        return pd.DataFrame()
    finally:
        db.close()

@st.cache_data(ttl=10)
def load_investment_data():
    """Load daily investment data from the database"""
    db = SessionLocal()
    try:
        # Get all investments
        investments = db.query(DailyInvestment).all()
        # Convert to DataFrame
        if investments:
            data = [{
                "id": i.id,
                "date": i.date,
                "amount": i.amount
            } for i in investments]
            return pd.DataFrame(data)
        return pd.DataFrame()
    finally:
        db.close()

def calculate_overall_stats():
    """Calculate overall trading statistics"""
    trades_df = load_trade_data()
    
    if trades_df.empty:
        return {
            "total_trades": 0,
            "open_trades": 0,
            "closed_trades": 0,
            "total_profit": 0,
            "win_rate": 0,
            "avg_profit": 0
        }
    
    open_trades = trades_df[trades_df['is_active'] == True]
    closed_trades = trades_df[trades_df['is_active'] == False]
    
    # Calculate win rate from closed trades
    winning_trades = 0
    if not closed_trades.empty:
        winning_trades = len(closed_trades[closed_trades['profit'] > 0])
    
    win_rate = winning_trades / len(closed_trades) * 100 if len(closed_trades) > 0 else 0
    
    # Calculate total profit
    total_profit = trades_df['profit'].sum()
    
    # Calculate average profit per trade
    avg_profit = total_profit / len(trades_df) if len(trades_df) > 0 else 0
    
    return {
        "total_trades": len(trades_df),
        "open_trades": len(open_trades),
        "closed_trades": len(closed_trades),
        "total_profit": total_profit,
        "win_rate": win_rate,
        "avg_profit": avg_profit
    }

def get_daily_investments_chart():
    """Create a chart showing daily investments"""
    investments_df = load_investment_data()
    
    if investments_df.empty:
        return None
    
    # Sort by date
    investments_df = investments_df.sort_values('date')
    
    # Create a line chart using plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=investments_df['date'],
        y=investments_df['amount'],
        mode='lines+markers',
        name='Daily Investment',
        line=dict(color='#1E88E5', width=2),
        marker=dict(size=8)
    ))
    
    # Add limit line
    if hasattr(config, 'DAILY_INVESTMENT_LIMIT'):
        fig.add_hline(
            y=config.DAILY_INVESTMENT_LIMIT,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Limit (${config.DAILY_INVESTMENT_LIMIT})",
            annotation_position="top right"
        )
    
    fig.update_layout(
        title='Daily Investments',
        xaxis_title='Date',
        yaxis_title='Amount ($)',
        height=400,
        xaxis=dict(
            tickformat='%d %b %Y'  # e.g., "01 Jul 2025"
        )
    )
    
    return fig

def get_profit_chart():
    """Create a chart showing profit over time"""
    trades_df = load_trade_data()
    
    if trades_df.empty:
        return None
    
    # Sort by time opened
    trades_df = trades_df.sort_values('time_open')
    
    # Convert time_open to datetime
    trades_df['time_open'] = pd.to_datetime(trades_df['time_open'], dayfirst=True, utc=True).dt.tz_convert(config.TIMEZONE)
    
    # Calculate cumulative profit
    trades_df['cumulative_profit'] = trades_df['profit'].cumsum()
    
    # Create a line chart using plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trades_df['time_open'],
        y=trades_df['cumulative_profit'],
        mode='lines',
        name='Cumulative Profit',
        line=dict(color='#4CAF50', width=2)
    ))
    
    fig.update_layout(
        title='Profit Over Time',
        xaxis_title='Date',
        yaxis_title='Profit ($)',
        height=400,
        xaxis=dict(
            tickformat='%d %b %Y'  # e.g., "01 Jul 2025"
        )
    )
    
    return fig

def run_bot_in_thread():
    """Run the trading bot in a separate thread"""
    global bot_instance
    
    bot_instance = TradingBot()
    
    def bot_thread_function():
        try:
            bot_instance.setup()
            
            while not stop_bot.is_set():
                try:
                    # Check for high-risk news events
                    high_risk = risk_guard.check_news_risk()
                    
                    if high_risk:
                        st.session_state.bot_status = "High risk detected - closing trades"
                        trade_executor.close_all_trades()
                    else:
                        st.session_state.bot_status = "No high risk detected - safe to trade"
                        # Process trades if no risk detected
                        bot_instance.trade_manager.process_trades()
                    
                    # Sleep interval between checks
                    for _ in range(config.CHECK_INTERVAL_SECONDS):
                        if stop_bot.is_set():
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    st.session_state.bot_status = f"Error: {str(e)}"
                    time.sleep(10)
        except Exception as e:
            st.session_state.bot_status = f"Fatal error: {str(e)}"
    
    return threading.Thread(target=bot_thread_function, daemon=True)

def main():
    """Main function to render the Streamlit UI"""
    global bot_thread, stop_bot
    
    # Initialize session state variables if they don't exist
    if 'bot_running' not in st.session_state:
        st.session_state.bot_running = False
    if 'bot_status' not in st.session_state:
        st.session_state.bot_status = "Bot not running"
    
    # Sidebar
    st.sidebar.markdown("## Bot Controls")
    
    if st.sidebar.button("Start Bot" if not st.session_state.bot_running else "Bot Running", 
                          disabled=st.session_state.bot_running):
        st.session_state.bot_running = True
        stop_bot.clear()
        bot_thread = run_bot_in_thread()
        bot_thread.start()
        st.session_state.bot_status = "Bot starting..."
    
    if st.sidebar.button("Stop Bot", disabled=not st.session_state.bot_running):
        if st.session_state.bot_running:
            st.session_state.bot_running = False
            stop_bot.set()
            if bot_thread and bot_thread.is_alive():
                bot_thread.join(timeout=2)
            st.session_state.bot_status = "Bot stopped"
    
    # Bot status indicator
    status_color = "🟢" if st.session_state.bot_running else "🔴"
    st.sidebar.markdown(f"### Status: {status_color} {st.session_state.bot_status}")
    
    # Database controls
    st.sidebar.markdown("## Database Controls")
    if st.sidebar.button("Initialize DB"):
        import init_db
        init_db.initialize_db()
        st.sidebar.success("Database initialized!")
    
    if st.sidebar.button("Reset DB"):
        import init_db
        init_db.reset_db()
        st.sidebar.success("Database reset!")
    
    # Config settings
    st.sidebar.markdown("## Config Settings")
    st.sidebar.info(f"Symbol: {config.SYMBOL}")
    st.sidebar.info(f"Daily Investment Limit: ${load_settings().get('investment_limit', config.DAILY_INVESTMENT_LIMIT)}")
    
    # Main area
    st.markdown("<h1 class='main-header'>Forex Trading Bot Dashboard</h1>", unsafe_allow_html=True)
    
    # Overall stats in a row
    stats = calculate_overall_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
        st.metric("Total Trades", stats["total_trades"])
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
        st.metric("Open Trades", stats["open_trades"])
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
        profit_class = "profit-positive" if stats["total_profit"] > 0 else "profit-negative"
        st.metric("Total Profit", f"${stats['total_profit']:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
        st.metric("Win Rate", f"{stats['win_rate']:.2f}%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Charts row
    st.markdown("<h2 class='sub-header'>Performance Charts</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        profit_chart = get_profit_chart()
        if profit_chart:
            st.plotly_chart(profit_chart, use_container_width=True)
        else:
            st.info("No trade data available to generate chart")
    
    with col2:
        investment_chart = get_daily_investments_chart()
        if investment_chart:
            st.plotly_chart(investment_chart, use_container_width=True)
        else:
            st.info("No investment data available to generate chart")
    
    # Trades table
    st.markdown("<h2 class='sub-header'>Active Trades</h2>", unsafe_allow_html=True)
    trades_df = load_trade_data()
    if not trades_df.empty:
        active_trades = trades_df[trades_df['is_active'] == True]
        if not active_trades.empty:
            st.dataframe(active_trades[["ticket", "symbol", "type", "volume", "price_open", "profit", "time_open"]], 
                         use_container_width=True, hide_index=True)
        else:
            st.info("No active trades")
    else:
        st.info("No trade data available")
    
    # Recent signals
    st.markdown("<h2 class='sub-header'>Recent Signals</h2>", unsafe_allow_html=True)
    signals_df = load_signal_data()
    if not signals_df.empty:
        # Show the most recent 10 signals
        recent_signals = signals_df.sort_values('timestamp', ascending=False).head(10)
        st.dataframe(recent_signals[["symbol", "signal_type", "confidence", "timestamp", "executed"]], 
                     use_container_width=True, hide_index=True)
    else:
        st.info("No signal data available")
    
if __name__ == "__main__":
    main()
