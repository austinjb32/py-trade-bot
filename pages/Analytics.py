"""
Analytics page for the Streamlit UI.
This page provides detailed trading analytics and performance metrics.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import pytz
from datetime import datetime
from db_config import SessionLocal
from models import Trade, Signal, MarketData
from timezone_utils import convert_utc_to_local, format_datetime
import config
from dashboard_components import (
    create_profit_by_pair_chart,
    create_trade_distribution_chart,
    create_daily_profit_chart,
    create_trade_duration_histogram,
    display_trade_stats_card
)

# Page configuration
st.set_page_config(
    page_title="Trading Analytics",
    page_icon="📊",
    layout="wide"
)

# Load data
@st.cache_data(ttl=10)
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
                # Convert UTC timestamps to user's timezone
                "time_open": format_datetime(convert_utc_to_local(t.time_open)),
                "time_close": format_datetime(convert_utc_to_local(t.time_close)) if t.time_close else None,
                "time_open_raw": t.time_open,  # Keep raw datetime for filtering
                "time_close_raw": t.time_close,  # Keep raw datetime for filtering
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
        signals = db.query(Signal).all()
        if signals:
            data = [{
                "id": s.id,
                "symbol": s.symbol,
                "signal_type": s.signal_type,
                "confidence": s.confidence,
                "reason": s.reason,
                # Convert UTC timestamp to user's timezone
                "timestamp": format_datetime(convert_utc_to_local(s.time_generated)),
                "timestamp_raw": s.time_generated,  # Keep raw datetime for filtering
                "executed": s.executed
            } for s in signals]
            return pd.DataFrame(data)
        return pd.DataFrame()
    finally:
        db.close()

@st.cache_data(ttl=10)
def load_market_data():
    """Load market data snapshots from the database with timezone conversion"""
    db = SessionLocal()
    try:
        market_data = db.query(MarketData).order_by(MarketData.time.desc()).all()
        if market_data:
            data = [{
                "id": md.id,
                "symbol": md.symbol,
                "bid": md.bid,
                "ask": md.ask,
                "spread": md.spread,
                # Convert UTC time to local timezone for display
                "time": format_datetime(convert_utc_to_local(md.time)),
                "time_raw": md.time,  # Keep raw time for filtering
                "balance": md.balance,
                "equity": md.equity,
                "margin": md.margin,
                "daily_profit_target": md.daily_profit_target,
                "current_daily_profit": md.current_daily_profit,
                "profit_target_achieved": "ACHIEVED" if md.profit_target_achieved else "NOT YET ACHIEVED",
                "predicted_profit": md.predicted_profit,
                "predicted_direction": md.predicted_direction
            } for md in market_data]
            return pd.DataFrame(data)
        return pd.DataFrame()
    finally:
        db.close()

def main():
    """Main function for analytics page"""
    st.title("Trading Analytics & Performance")
    
    # Show current timezone
    st.caption(f"All timestamps displayed in {config.TIMEZONE} timezone")
    
    # Load data
    trades_df = load_trade_data()
    signals_df = load_signal_data()
    market_df = load_market_data()
    
    if trades_df.empty:
        st.info("No trade data available for analysis")
        return
    
    # Filter options
    st.sidebar.header("Filter Options")
    
    # Date range filter
    if not trades_df.empty:
        min_date = pd.to_datetime(trades_df['time_open_raw']).min().date()
        max_date = pd.to_datetime(trades_df['time_open_raw']).max().date()
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            trades_df = trades_df[
                (pd.to_datetime(trades_df['time_open_raw']).dt.date >= start_date) &
                (pd.to_datetime(trades_df['time_open_raw']).dt.date <= end_date)
            ]
    
    # Symbol filter
    if not trades_df.empty:
        symbols = ["All"] + list(trades_df['symbol'].unique())
        selected_symbol = st.sidebar.selectbox("Select Symbol", symbols)
        
        if selected_symbol != "All":
            trades_df = trades_df[trades_df['symbol'] == selected_symbol]
    
    # Trade type filter
    if not trades_df.empty:
        trade_types = ["All", "BUY", "SELL"]
        selected_type = st.sidebar.selectbox("Trade Type", trade_types)
        
        if selected_type != "All":
            trades_df = trades_df[trades_df['type'] == selected_type]
    
    # Active/Closed filter
    if not trades_df.empty:
        trade_status = ["All", "Active", "Closed"]
        selected_status = st.sidebar.selectbox("Trade Status", trade_status)
        
        if selected_status == "Active":
            trades_df = trades_df[trades_df['is_active'] == True]
        elif selected_status == "Closed":
            trades_df = trades_df[trades_df['is_active'] == False]
    
    # Display metrics and charts
    col1, col2 = st.columns([1, 3])
    
    with col1:
        display_trade_stats_card()
    
    with col2:
        # Key metrics in a row
        metrics_cols = st.columns(4)
        
        if not trades_df.empty:
            # Total trades
            metrics_cols[0].metric("Total Trades", len(trades_df))
            
            # Average profit
            avg_profit = trades_df['profit'].mean() if len(trades_df) > 0 else 0
            metrics_cols[1].metric("Avg. Profit per Trade", f"${avg_profit:.2f}")
            
            # Win rate (for closed trades)
            closed_trades = trades_df[trades_df['is_active'] == False]
            winning_trades = closed_trades[closed_trades['profit'] > 0]
            win_rate = len(winning_trades) / len(closed_trades) * 100 if len(closed_trades) > 0 else 0
            metrics_cols[2].metric("Win Rate", f"{win_rate:.2f}%")
            
            # Total profit
            total_profit = trades_df['profit'].sum()
            metrics_cols[3].metric("Total Profit", f"${total_profit:.2f}")
    
    # Charts
    st.subheader("Performance Analysis")
    
    if not trades_df.empty:
        # First row of charts
        row1_cols = st.columns(2)
        
        with row1_cols[0]:
            daily_profit_chart = create_daily_profit_chart(trades_df)
            if daily_profit_chart:
                st.plotly_chart(daily_profit_chart, use_container_width=True)
        
        with row1_cols[1]:
            profit_by_pair_chart = create_profit_by_pair_chart(trades_df)
            if profit_by_pair_chart:
                st.plotly_chart(profit_by_pair_chart, use_container_width=True)
        
        # Second row of charts
        row2_cols = st.columns(2)
        
        with row2_cols[0]:
            distribution_chart = create_trade_distribution_chart(trades_df)
            if distribution_chart:
                st.plotly_chart(distribution_chart, use_container_width=True)
        
        with row2_cols[1]:
            duration_chart = create_trade_duration_histogram(trades_df)
            if duration_chart:
                st.plotly_chart(duration_chart, use_container_width=True)
            else:
                st.info("No closed trades available for duration analysis")
    
    # Detailed trade data
    st.subheader("Trade History")
    if not trades_df.empty:
        st.dataframe(
            trades_df.sort_values('time_open', ascending=False),
            use_container_width=True,
            column_config={
                "profit": st.column_config.NumberColumn(
                    "Profit",
                    help="Trade profit in dollars",
                    format="$%.2f"
                ),
                "time_open": "Open Time",
                "time_close": "Close Time",
                "is_active": "Active"
            },
            hide_index=True
        )
    else:
        st.info("No trades match the selected filters")
    
    # Signal analysis
    st.subheader("Signal Analysis")
    if not signals_df.empty:
        # Filter signals based on date range if set
        if len(date_range) == 2:
            start_date, end_date = date_range
            signals_df = signals_df[
                (pd.to_datetime(signals_df['timestamp_raw']).dt.date >= start_date) &
                (pd.to_datetime(signals_df['timestamp_raw']).dt.date <= end_date)
            ]
        
        # Count signals by type
        signal_counts = signals_df['signal_type'].value_counts()
        
        # Create pie chart
        fig = px.pie(
            names=signal_counts.index,
            values=signal_counts.values,
            title="Signal Distribution by Type"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Signal execution rate
        executed_signals = len(signals_df[signals_df['executed'] == True])
        execution_rate = executed_signals / len(signals_df) * 100 if len(signals_df) > 0 else 0
        
        st.metric("Signal Execution Rate", f"{execution_rate:.2f}%")
        
        # Display signals
        st.dataframe(
            signals_df.sort_values('timestamp', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No signal data available")
        
    # Market Data Analysis
    st.subheader("Market Data Snapshots")
    if not market_df.empty:
        # Filter market data based on date range if set
        if 'date_range' in locals() and len(date_range) == 2:
            start_date, end_date = date_range
            market_df = market_df[
                (pd.to_datetime(market_df['time_raw']).dt.date >= start_date) &
                (pd.to_datetime(market_df['time_raw']).dt.date <= end_date)
            ]
            
        # Profit Target Tracking
        st.markdown("### Profit Target Analysis")
        
        # Create columns for metrics
        profit_cols = st.columns(3)
        
        # Get the latest market data entry
        latest_data = market_df.iloc[0] if len(market_df) > 0 else None
        
        if latest_data is not None:
            # Display current profit target metrics
            profit_cols[0].metric(
                "Daily Profit Target", 
                f"${latest_data['daily_profit_target']:.2f}"
            )
            
            profit_cols[1].metric(
                "Current Daily Profit", 
                f"${latest_data['current_daily_profit']:.2f}",
                delta=f"{latest_data['current_daily_profit'] - latest_data['daily_profit_target']:.2f}"
            )
            
            profit_cols[2].metric(
                "Target Status", 
                latest_data['profit_target_achieved']
            )
            
            # Create profit tracking chart
            if len(market_df) > 1:
                st.markdown("#### Daily Profit Progression")
                
                # Convert time to datetime for plotting
                plot_df = market_df.copy()
                plot_df['time_dt'] = pd.to_datetime(plot_df['time_raw'], utc=True).dt.tz_convert(config.TIMEZONE)
                
                # Sort by time
                plot_df = plot_df.sort_values('time_dt')
                
                # Create plot
                fig = go.Figure()
                
                # Add profit line
                fig.add_trace(go.Scatter(
                    x=plot_df['time_dt'],
                    y=plot_df['current_daily_profit'],
                    mode='lines+markers',
                    name='Daily Profit'
                ))
                
                # Add target line
                fig.add_trace(go.Scatter(
                    x=plot_df['time_dt'],
                    y=plot_df['daily_profit_target'],
                    mode='lines',
                    name='Target',
                    line=dict(dash='dash', color='green')
                ))
                
                # Layout
                fig.update_layout(
                    title="Daily Profit vs Target",
                    xaxis_title="Time",
                    yaxis_title="Profit ($)",
                    legend_title="Legend",
                    xaxis=dict(
                        tickformat='%d %b %Y %H:%M:%S'  # e.g., "01 Jul 2025 22:50"
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Market Data Table
        st.markdown("### Market Data History")
        if not market_df.empty:
            # Display important columns
            display_cols = [
                'symbol', 'bid', 'ask', 'spread', 'time', 
                'balance', 'equity', 'current_daily_profit', 
                'profit_target_achieved', 'predicted_profit'
            ]
            
            st.dataframe(
                market_df[display_cols].sort_values('time_raw', ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No market data available for the selected period")

if __name__ == "__main__":
    main()
