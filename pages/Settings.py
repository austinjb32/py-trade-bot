"""
Settings page for the Forex Trading Bot.
This page allows configuration of bot parameters and system settings.
"""
import streamlit as st
import os
import json
import time
import pytz
from datetime import datetime
from pathlib import Path
import config
from dashboard_components import display_system_status

# Page configuration
st.set_page_config(
    page_title="Bot Settings",
    page_icon="⚙️",
    layout="wide"
)

def backup_config():
    """Create a backup of the current config.py file"""
    import shutil
    import datetime
    
    try:
        config_path = Path("config.py")
        if config_path.exists():
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path(f"config_backup_{timestamp}.py")
            
            # Create backup
            shutil.copy2(config_path, backup_path)
            return True, backup_path
        return False, None
    except Exception as e:
        print(f"Backup error: {e}")
        return False, None

def save_settings(settings_dict):
    """Save settings to a JSON file and update config.py"""
    # Save to JSON file for persistence
    settings_path = Path("bot_settings.json")
    try:
        # First create a backup of the config file
        backup_success, backup_path = backup_config()
        
        # Save to JSON
        with open(settings_path, 'w') as f:
            json.dump(settings_dict, f, indent=2)
        
        # Update config.py file
        config_path = Path("config.py")
        if config_path.exists():
            # Read existing config file
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            # Update the values one by one
            for key, value in settings_dict.items():
                # Convert key to uppercase for config.py format
                config_key = key.upper()
                
                # Special handling for different types of values
                if isinstance(value, str):
                    if key in ['system_prompt']:
                        # Multi-line string with proper indentation for system prompt
                        new_value = f'"""{value}\n"""'
                    else:
                        # Regular string with quotes
                        new_value = f'"{value}"'
                elif isinstance(value, bool):
                    new_value = str(value)
                elif isinstance(value, (int, float)):
                    new_value = str(value)
                else:
                    new_value = str(value)
                
                # Replace in config file using regex pattern matching
                import re
                pattern = rf'^{config_key}\s*=\s*.*$'
                replacement = f'{config_key} = {new_value}'
                
                # Use regex with multiline mode to match entire lines
                config_content = re.sub(pattern, replacement, config_content, flags=re.MULTILINE)
            
            # Write updated config back to file
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            result = {
                "success": True,
                "backup": {
                    "created": backup_success,
                    "path": str(backup_path) if backup_path else None
                }
            }    
            return result
        else:
            return {"success": False, "error": "Config file not found"}
    except Exception as e:
        error_msg = f"Error saving settings: {e}"
        print(error_msg)
        return {"success": False, "error": error_msg}

def load_settings():
    """Load settings from JSON file if it exists"""
    settings_path = Path("bot_settings.json")
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            return json.load(f)
    return {}

def reset_to_defaults():
    """Reset settings to default values"""
    try:
        # Create a dictionary with default values
        defaults = {
            "mt5_account": 213481261,
            "mt5_password": "u8syB$rA",
            "mt5_server": "OctaFX-Demo",
            "together_api_key": "tgp_v1_El075FW8IMaU9Fl1q7fFONUZ2G7KV59eLWPuFaJO3h0",
            "finnhub_api_key": "d1hc7v9r01qsvr298pugd1hc7v9r01qsvr298pv0",
            "together_model": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
            "symbol": "EURUSD",
            "base_lot": 0.01,
            "daily_profit_target": 20.0,
            "daily_investment_limit": 20.0,
            "check_interval_seconds": 300,
            "region": "India",
            "timezone": "Asia/Kolkata",
            "system_prompt": """
You are a professional forex trading advisor with expertise in EUR/USD trading.

Your role is to analyze the provided market data and current positions to make a clear trading recommendation.

Consider these key factors when making your decision:
1. Current market trend and momentum
2. Spread and transaction costs
3. Existing positions and their profitability
4. Risk management (avoid overexposure in one direction)

Be disciplined and conservative with your recommendations. 
Don't chase losses or suggest doubling down on losing positions.
Only recommend entering the market when conditions are favorable.
No other information should be provided.
"""
        }
        
        # Save these defaults
        result = save_settings(defaults)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Main function for settings page"""
    st.title("Trading Bot Settings")
    st.caption("Configure all aspects of your trading bot in one place")
    
    # Load existing settings
    settings = load_settings()
    
    # System status at the top
    with st.expander("System Status", expanded=False):
        display_system_status()
    
    # Create tabs for different setting categories
    tabs = st.tabs([
        "💻 Database", 
        "🔑 Credentials",
        "🤖 AI & Trading", 
        "🕒 Region & Timezone",
        "⚙️ Advanced"
    ])
    
    # Tab 1: Database Settings
    with tabs[0]:
        st.header("Database Connection Settings")
        col1, col2 = st.columns(2)
        
        # Initialize a dictionary to collect database settings
        db_settings = {}
        
        with col1:
            # Database host
            db_host = st.text_input(
                "Database Host", 
                value=settings.get('db_host', os.environ.get("DB_HOST", "localhost")),
                help="PostgreSQL database host",
                key="db_host_input"
            )
            db_settings['db_host'] = db_host
            
            # Database port
            db_port = st.text_input(
                "Database Port",
                value=settings.get('db_port', os.environ.get("DB_PORT", "5432")),
                help="PostgreSQL database port",
                key="db_port_input"
            )
            db_settings['db_port'] = db_port
            
        with col2:
            # Database name
            db_name = st.text_input(
                "Database Name",
                value=settings.get('db_name', os.environ.get("DB_NAME", "tradebot")),
                help="PostgreSQL database name",
                key="db_name_input"
            )
            db_settings['db_name'] = db_name
            
            # Database user
            db_user = st.text_input(
                "Database User",
                value=settings.get('db_user', os.environ.get("DB_USER", "postgres")),
                help="PostgreSQL database user",
                key="db_user_input"
            )
            db_settings['db_user'] = db_user
        
        # Database password
        db_password = st.text_input(
            "Database Password",
            value=settings.get('db_password', os.environ.get("DB_PASSWORD", "")),
            type="password",
            help="PostgreSQL database password",
            key="db_password_input"
        )
        db_settings['db_password'] = db_password
        
        # Generate .env file button
        st.markdown("---")
        st.subheader("Environment File")
        
        if st.button("Generate .env File", key="gen_env_file"):
            env_content = f"""# Database settings
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
"""
            try:
                with open(".env", "w") as f:
                    f.write(env_content)
                st.success("✅ .env file generated successfully!")
                st.code(env_content, language="bash")
            except Exception as e:
                st.error(f"❌ Error generating .env file: {str(e)}")
    
    # Tab 2: Credentials
    with tabs[1]:
        st.header("MetaTrader 5 Credentials")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # MT5 Account
            mt5_account = st.text_input(
                "MT5 Account Number",
                value=str(settings.get('mt5_account', config.MT5_ACCOUNT)) if hasattr(config, 'MT5_ACCOUNT') else '',
                help="Your MetaTrader 5 account number",
                key="mt5_account_input"
            )
        
        with col2:
            # MT5 Server
            mt5_server = st.text_input(
                "MT5 Server",
                value=settings.get('mt5_server', config.MT5_SERVER) if hasattr(config, 'MT5_SERVER') else '',
                help="MetaTrader 5 server name",
                key="mt5_server_input"
            )
        
        # MT5 Password
        mt5_password = st.text_input(
            "MT5 Password",
            value=settings.get('mt5_password', config.MT5_PASSWORD) if hasattr(config, 'MT5_PASSWORD') else '',
            type="password",
            help="MetaTrader 5 password (stored securely)",
            key="mt5_password_input"
        )
        
        st.markdown("---")
        st.header("API Keys")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Together AI API Key
            together_api_key = st.text_input(
                "Together AI API Key",
                value=settings.get('together_api_key', config.TOGETHER_API_KEY) if hasattr(config, 'TOGETHER_API_KEY') else '',
                type="password",
                help="API key for Together AI LLM services",
                key="together_api_key_input"
            )
        
        with col2:
            # Finnhub API Key
            finnhub_api_key = st.text_input(
                "Finnhub API Key",
                value=settings.get('finnhub_api_key', config.FINNHUB_API_KEY) if hasattr(config, 'FINNHUB_API_KEY') else '',
                type="password",
                help="API key for Finnhub financial data",
                key="finnhub_api_key_input"
            )
    
    # Tab 3: AI & Trading
    with tabs[2]:
        st.header("LLM Model Settings")
        
        # Model selection
        models = settings.get('models', config.MODELS)
        selected_model = st.selectbox(
            "LLM Model",
            models,
            index=models.index(settings.get('together_model', config.TOGETHER_MODEL)) if hasattr(config, 'TOGETHER_MODEL') and config.TOGETHER_MODEL in models else 0,
            help="AI model to use for trading decisions",
            key="model_selection_input"
        )
        
        # System prompt
        default_prompt = getattr(config, 'SYSTEM_PROMPT', '')
        system_prompt = st.text_area(
            "System Prompt",
            value=settings.get('system_prompt', default_prompt),
            height=200,
            help="Instructions for the AI when making trading decisions",
            key="system_prompt_input"
        )
        
        st.markdown("---")
        st.header("Trading Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Symbol selection
            symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]
            symbol = st.selectbox(
                "Trading Symbol", 
                symbols, 
                index=symbols.index(settings.get('symbol', config.SYMBOL)) if hasattr(config, 'SYMBOL') and config.SYMBOL in symbols else 0,
                help="Primary currency pair for trading",
                key="symbol_selection_input"
            )
            
            # Base lot size
            base_lot = st.number_input(
                "Base Lot Size",
                value=float(settings.get('base_lot', config.BASE_LOT)) if hasattr(config, 'BASE_LOT') else 0.01,
                min_value=0.01,
                max_value=0.1,
                step=0.01,
                format="%.2f",
                help="Base lot size for trades (e.g., 0.01 = micro lot)",
                key="base_lot_input"
            )
        
        with col2:
            # Daily profit target
            daily_profit_target = st.number_input(
                "Daily Profit Target ($)",
                value=float(settings.get('daily_profit_target', config.DAILY_PROFIT_TARGET)) if hasattr(config, 'DAILY_PROFIT_TARGET') else 20.0,
                min_value=0.0,
                step=1.0,
                format="%.2f",
                help="Daily profit target in USD",
                key="profit_target_input"
            )
            
            # Daily investment limit
            daily_investment_limit = st.number_input(
                "Daily Investment Limit ($)",
                value=float(settings.get('daily_investment_limit', config.DAILY_INVESTMENT_LIMIT)) if hasattr(config, 'DAILY_INVESTMENT_LIMIT') else 20.0,
                min_value=0.0,
                step=1.0,
                format="%.2f",
                help="Maximum daily investment amount in USD",
                key="investment_limit_input"
            )
        
        # Check interval
        check_interval = st.number_input(
            "Market Check Interval (seconds)",
            value=int(settings.get('check_interval_seconds', config.CHECK_INTERVAL_SECONDS)) if hasattr(config, 'CHECK_INTERVAL_SECONDS') else 300,
            min_value=10,
            step=10,
            help="How often the bot checks market conditions (in seconds)",
            key="check_interval_input"
        )
    
    # Tab 4: Region & Timezone
    with tabs[3]:
        st.header("Region & Timezone Settings")
        
        # Region selection
        regions = ["India", "US", "UK", "Europe", "Japan", "Australia", "Other"]
        selected_region = st.selectbox(
            "Region",
            regions,
            index=regions.index(settings.get('region', config.REGION)) if hasattr(config, 'REGION') and config.REGION in regions else 0,
            help="Select your geographic region",
            key="region_selection_input"
        )
        
        # Get timezones based on region
        region_timezones = {
            "India": ["Asia/Kolkata"],
            "US": ["US/Eastern", "US/Central", "US/Mountain", "US/Pacific", "US/Alaska", "US/Hawaii"],
            "UK": ["Europe/London"],
            "Europe": ["Europe/Paris", "Europe/Berlin", "Europe/Madrid", "Europe/Rome", "Europe/Amsterdam", "Europe/Zurich"],
            "Japan": ["Asia/Tokyo"],
            "Australia": ["Australia/Sydney", "Australia/Melbourne", "Australia/Perth", "Australia/Brisbane"],
            "Other": ["UTC", "Etc/GMT"]
        }
        
        # Filter timezones by region
        available_timezones = region_timezones.get(selected_region, ["UTC"])
        
        # Timezone selection
        selected_timezone = st.selectbox(
            "Timezone",
            available_timezones,
            index=available_timezones.index(settings.get('timezone', config.TIMEZONE)) 
                if hasattr(config, 'TIMEZONE') and config.TIMEZONE in available_timezones 
                else 0,
            help="Select your timezone for date/time displays",
            key="timezone_selection_input"
        )
        
        # Show current time in selected timezone
        try:
            current_time = datetime.now(pytz.timezone(selected_timezone))
            st.info(f"Current time in {selected_timezone}: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            st.error(f"Error displaying time: {str(e)}")
            
        st.markdown("---")
        st.info("📅 All dates and times throughout the application will be displayed in this timezone. Data is still stored in UTC in the database.")
    
    # Tab 5: Advanced
    with tabs[4]:
        st.header("Advanced Settings")
        
        # Reset to defaults option
        st.subheader("Reset to Default Settings")
        st.warning("⚠️ This will reset ALL settings to their default values. This action cannot be undone.")
        
        if st.button("🔄 Reset All Settings to Defaults", key="reset_defaults"):
            confirm = st.checkbox("I confirm I want to reset all settings", key="confirm_reset")
            if confirm:
                result = reset_to_defaults()
                if result.get("success", False):
                    st.success("✅ Settings have been reset to defaults. Reload the page to see the changes.")
                    # Add button to reload page
                    if st.button("🔄 Reload Page", key="reload_after_reset"):
                        st.experimental_rerun()
                else:
                    st.error(f"❌ Failed to reset settings: {result.get('error', 'Unknown error')}")
        
        # Backup current config
        st.subheader("Backup Current Configuration")
        if st.button("📁 Create Config Backup", key="backup_now"):
            success, backup_path = backup_config()
            if success:
                st.success(f"✅ Backup created successfully at: {backup_path}")
            else:
                st.error("❌ Failed to create backup")
                
        # View raw settings
        st.subheader("View Raw Settings")
        if st.checkbox("Show Raw Settings JSON", key="show_raw"):
            st.code(json.dumps(settings, indent=2), language="json")
            
        # View config.py content
        st.subheader("View config.py Content")
        if st.checkbox("Show config.py Content", key="show_config"):
            try:
                with open("config.py", "r") as f:
                    config_content = f.read()
                st.code(config_content, language="python")
            except Exception as e:
                st.error(f"Error reading config.py: {str(e)}")
    
    # Save All Settings Button (outside tabs, always visible)
    st.markdown("---")
    st.subheader("💾 Save All Settings")
    
    # Add a brief summary of what will be saved
    st.markdown("The following settings will be saved to both `bot_settings.json` and `config.py`:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Database**")
        st.markdown("- Host, Port, Name")
        st.markdown("- Username, Password")
        
    with col2:
        st.markdown("**Credentials & Trading**")
        st.markdown("- MT5 Account, API Keys")
        st.markdown("- Trading Symbol, Lot Size")
        st.markdown("- Profit Target, Check Interval")
        
    with col3:
        st.markdown("**Other**")
        st.markdown("- LLM Model & System Prompt")
        st.markdown("- Region & Timezone")
        st.markdown("- Investment Limits")
    
    # Confirmation checkbox for sensitive info
    confirm_save = st.checkbox("I understand that sensitive information like passwords and API keys will be saved to config.py", key="confirm_save")
    
    # Save button
    if st.button("💾 Save All Settings", type="primary", key="save_all_settings", disabled=not confirm_save):
        try:
            with st.spinner("Saving settings..."):
                # Collect all settings
                all_settings = {
                    # MT5 Settings
                    "mt5_account": int(mt5_account) if mt5_account.strip() else config.MT5_ACCOUNT,
                    "mt5_password": mt5_password,
                    "mt5_server": mt5_server,
                    
                    # API Keys
                    "together_api_key": together_api_key,
                    "finnhub_api_key": finnhub_api_key,
                    
                    # LLM Settings
                    "together_model": selected_model,
                    "system_prompt": system_prompt,
                    
                    # Trading Parameters
                    "symbol": symbol,
                    "base_lot": float(base_lot),
                    "daily_profit_target": float(daily_profit_target),
                    "daily_investment_limit": float(daily_investment_limit),
                    "check_interval_seconds": int(check_interval),
                    
                    # Region and Timezone
                    "region": selected_region,
                    "timezone": selected_timezone
                }
                
                # Add database settings
                all_settings.update(db_settings)
                
                # Save all settings
                result = save_settings(all_settings)
                
                if result.get("success", False):
                    st.success("✅ All settings saved successfully!")
                    backup_info = result.get("backup", {})
                    if backup_info.get("created", False):
                        st.info(f"A backup of the previous configuration was created at: {backup_info.get('path')}")
                    st.info("Note: Some settings may require restarting the Streamlit application to take effect.")
                else:
                    st.error(f"❌ Failed to save settings: {result.get('error', 'Unknown error')}")
                    
            # Add a reload button
            if st.button("🔄 Reload Page", key="reload_after_save"):
                st.experimental_rerun()
                    
        except Exception as e:
            st.error(f"Error saving settings: {str(e)}")
            st.info("Please ensure all fields contain valid values.")
    
    st.markdown("---")
    st.caption("📝 Settings are saved to both `bot_settings.json` and `config.py` for persistence.")

if __name__ == "__main__":
    main()
