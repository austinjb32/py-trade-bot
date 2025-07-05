"""
Timezone utility functions for the trading bot.
Handles conversion between UTC and configured timezone.
"""
import pytz
from datetime import datetime
import config

def convert_utc_to_local(utc_dt):
    """
    Convert a UTC datetime to the configured local timezone.
    
    Args:
        utc_dt: A datetime object in UTC timezone (can be naive or tz-aware)
        
    Returns:
        A datetime object converted to the configured timezone
    """
    if utc_dt is None:
        return None
        
    # Ensure the datetime is timezone-aware UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)
    elif utc_dt.tzinfo != pytz.UTC:
        utc_dt = utc_dt.astimezone(pytz.UTC)
    
    # Convert to configured timezone
    local_tz = pytz.timezone(config.TIMEZONE)
    return utc_dt.astimezone(local_tz)

def convert_local_to_utc(local_dt):
    """
    Convert a datetime in the configured local timezone to UTC.
    
    Args:
        local_dt: A datetime object in the configured timezone (can be naive or tz-aware)
        
    Returns:
        A datetime object converted to UTC timezone
    """
    if local_dt is None:
        return None
        
    # If naive, assume it's in the configured timezone
    local_tz = pytz.timezone(config.TIMEZONE)
    if local_dt.tzinfo is None:
        local_dt = local_tz.localize(local_dt)
    elif local_dt.tzinfo != local_tz:
        # If it has a different timezone, convert it to the local timezone first
        local_dt = local_dt.astimezone(local_tz)
    
    # Convert to UTC
    return local_dt.astimezone(pytz.UTC)

def get_current_local_time():
    """
    Get the current time in the configured timezone.
    
    Returns:
        A datetime object representing the current time in the configured timezone
    """
    now_utc = datetime.now(pytz.UTC)
    local_tz = pytz.timezone(config.TIMEZONE)
    return now_utc.astimezone(local_tz)

def format_datetime(dt, format_str="%Y-%m-%d %H:%M:%S %Z"):
    """
    Format a datetime object to a string representation.
    
    Args:
        dt: The datetime object to format
        format_str: The format string to use
        
    Returns:
        A string representation of the datetime
    """
    if dt is None:
        return "N/A"
    
    # If the datetime is naive, assume it's in UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # Always convert to local timezone for display
    local_dt = convert_utc_to_local(dt)
    return local_dt.strftime(format_str)
