"""
Dashboard components for the Streamlit UI.
This module contains utility functions for creating Streamlit UI components.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from config import TIMEZONE
from models import Trade, Signal, DailyInvestment
from db_config import SessionLocal


def create_profit_by_pair_chart(trades_df):
    """
    Create a bar chart showing profit by currency pair
    """
    if trades_df.empty:
        return None
    
    # Group by symbol and sum profit
    profit_by_pair = trades_df.groupby('symbol')['profit'].sum().reset_index()
    
    # Create bar chart
    fig = px.bar(
        profit_by_pair, 
        x='symbol', 
        y='profit',
        title='Profit by Currency Pair',
        color='profit',
        color_continuous_scale=['#F44336', '#FFEB3B', '#4CAF50'],  # Red to Green
        labels={'symbol': 'Currency Pair', 'profit': 'Profit ($)'}
    )
    
    fig.update_layout(height=400)
    return fig


def create_trade_distribution_chart(trades_df):
    """
    Create a pie chart showing distribution of trades by type (BUY/SELL)
    """
    if trades_df.empty:
        return None
    
    # Count trades by type
    trade_counts = trades_df['type'].value_counts().reset_index()
    trade_counts.columns = ['type', 'count']
    
    # Create pie chart
    fig = px.pie(
        trade_counts, 
        values='count', 
        names='type',
        title='Trade Distribution (BUY/SELL)',
        color='type',
        color_discrete_map={'BUY': '#4CAF50', 'SELL': '#F44336'}
    )
    
    fig.update_layout(height=350)
    return fig


def create_daily_profit_chart(trades_df):
    """
    Create a bar chart showing daily profit
    """
    if trades_df.empty:
        return None
    
    # Convert time_open to date only
    trades_df['date'] = pd.to_datetime(trades_df['time_open_raw'], dayfirst=True, utc=True).dt.tz_convert(TIMEZONE).dt.date
    
    # Group by date and sum profit
    daily_profit = trades_df.groupby('date')['profit'].sum().reset_index()
    
    # Create bar chart
    fig = px.bar(
        daily_profit, 
        x='date', 
        y='profit',
        title='Daily Profit',
        color='profit',
        color_continuous_scale=['#F44336', '#FFEB3B', '#4CAF50'],  # Red to Green
        labels={'date': 'Date', 'profit': 'Profit ($)'}
    )
    
    fig.update_layout(height=350, xaxis=dict(tickformat='%d %b %Y'))
    return fig


def create_trade_duration_histogram(trades_df):
    """
    Create a histogram showing trade duration for closed trades
    """
    # Filter for closed trades
    closed_trades = trades_df[trades_df['is_active'] == False].copy()
    
    if closed_trades.empty:
        return None
    
    # Calculate duration in hours
    closed_trades['time_open'] = pd.to_datetime(closed_trades['time_open'])
    closed_trades['time_close'] = pd.to_datetime(closed_trades['time_close'])
    closed_trades['duration_hours'] = (closed_trades['time_close'] - closed_trades['time_open']).dt.total_seconds() / 3600
    
    # Create histogram
    fig = px.histogram(
        closed_trades, 
        x='duration_hours',
        nbins=20,
        title='Trade Duration Distribution',
        labels={'duration_hours': 'Duration (hours)'}
    )
    
    fig.update_layout(height=350)
    return fig


def display_trade_stats_card():
    """Display a card with trading statistics"""
    db = SessionLocal()
    try:
        # Get all trades
        trades = db.query(Trade).all()
        
        if not trades:
            st.info("No trade data available")
            return
        
        # Calculate statistics
        total_trades = len(trades)
        active_trades = sum(1 for t in trades if t.is_active)
        closed_trades = total_trades - active_trades
        
        winning_trades = sum(1 for t in trades if not t.is_active and t.profit > 0)
        losing_trades = sum(1 for t in trades if not t.is_active and t.profit < 0)
        
        win_rate = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0
        
        total_profit = sum(t.profit for t in trades)
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        # Calculate largest win and loss
        largest_win = max([t.profit for t in trades if not t.is_active] or [0])
        largest_loss = min([t.profit for t in trades if not t.is_active] or [0])
        
        # Create card
        st.markdown("""
        <style>
        .stat-card {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 5px;
        }
        .stat-label {
            font-weight: 500;
            color: #424242;
        }
        .stat-value {
            font-weight: 600;
            color: #1E88E5;
        }
        .positive-value {
            color: #4CAF50;
        }
        .negative-value {
            color: #F44336;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        
        st.markdown("<h3>Trading Performance</h3>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='stat-row'>
            <span class='stat-label'>Total Trades</span>
            <span class='stat-value'>{total_trades}</span>
        </div>
        <div class='stat-row'>
            <span class='stat-label'>Win Rate</span>
            <span class='stat-value'>{win_rate:.2f}%</span>
        </div>
        <div class='stat-row'>
            <span class='stat-label'>Total Profit</span>
            <span class='stat-value {"positive-value" if total_profit > 0 else "negative-value"}'>
                ${total_profit:.2f}
            </span>
        </div>
        <div class='stat-row'>
            <span class='stat-label'>Avg. Profit per Trade</span>
            <span class='stat-value {"positive-value" if avg_profit > 0 else "negative-value"}'>
                ${avg_profit:.2f}
            </span>
        </div>
        <div class='stat-row'>
            <span class='stat-label'>Largest Win</span>
            <span class='stat-value positive-value'>${largest_win:.2f}</span>
        </div>
        <div class='stat-row'>
            <span class='stat-label'>Largest Loss</span>
            <span class='stat-value negative-value'>${largest_loss:.2f}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    finally:
        db.close()


def create_bot_control_panel():
    """Create a control panel for bot settings"""
    import config
    
    st.markdown("### Bot Control Panel")
    
    # Symbol selection
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]
    selected_symbol = st.selectbox("Trading Symbol", symbols, index=symbols.index(config.SYMBOL) if config.SYMBOL in symbols else 0)
    
    # Investment limit
    default_limit = 20.0
    if hasattr(config, 'DAILY_INVESTMENT_LIMIT'):
        default_limit = config.DAILY_INVESTMENT_LIMIT
    
    investment_limit = st.slider("Daily Investment Limit ($)", 
                                min_value=5.0, 
                                max_value=100.0, 
                                value=default_limit, 
                                step=5.0)
    
    # Check interval
    default_interval = 300
    if hasattr(config, 'CHECK_INTERVAL_SECONDS'):
        default_interval = config.CHECK_INTERVAL_SECONDS
    
    check_interval = st.slider("Check Interval (seconds)", 
                              min_value=60, 
                              max_value=900, 
                              value=default_interval, 
                              step=60)
    
    # Base lot size
    default_lot = 0.01
    if hasattr(config, 'BASE_LOT'):
        default_lot = config.BASE_LOT
    
    base_lot = st.number_input("Base Lot Size", 
                              min_value=0.01, 
                              max_value=0.1, 
                              value=float(default_lot), 
                              step=0.01,
                              format="%.2f")
    
    # Apply button
    if st.button("Apply Settings"):
        # This is just a demonstration - in a real app you'd update the config file or database
        st.session_state.symbol = selected_symbol
        st.session_state.investment_limit = investment_limit
        st.session_state.check_interval = check_interval
        st.session_state.base_lot = base_lot
        
        st.success("Settings applied!")
        
        # Show current settings
        st.markdown("#### Current Settings")
        st.code(f"""
        SYMBOL = '{selected_symbol}'
        DAILY_INVESTMENT_LIMIT = {investment_limit}
        CHECK_INTERVAL_SECONDS = {check_interval}
        BASE_LOT = {base_lot}
        """)
    
    return {
        "symbol": selected_symbol,
        "investment_limit": investment_limit,
        "check_interval": check_interval,
        "base_lot": base_lot
    }


def display_system_status():
    """Display system status information"""
    import datetime
    import MetaTrader5 as mt5
    
    st.markdown("### System Status")
    
    # Current time
    now = datetime.datetime.now()
    
    # MT5 connection status
    mt5_initialized = False
    try:
        mt5_initialized = mt5.initialize()
    except:
        pass
    
    # Database connection status
    db_status = "Unknown"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_status = "Connected"
        db.close()
    except:
        db_status = "Disconnected"
    
    # Create status table
    status_data = {
        "Component": ["System Time", "MT5 Connection", "Database Connection"],
        "Status": [
            now.strftime("%Y-%m-%d %H:%M:%S"),
            "Connected" if mt5_initialized else "Disconnected",
            db_status
        ]
    }
    
    status_df = pd.DataFrame(status_data)
    
    # Display with colored status
    st.dataframe(
        status_df,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Current connection status",
                default="Unknown"
            )
        },
        hide_index=True,
        use_container_width=True
    )
