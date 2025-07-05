# news_fetcher.py

import requests
import json
import datetime
import time
from typing import List, Dict, Any, Optional, Union

def get_latest_headlines(count: int = 5, max_retries: int = 3) -> str:
    """
    Fetch latest forex calendar events from FairEconomy API.
    Returns formatted headlines with high impact events prioritized.
    
    Args:
        count: Number of headlines to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        String with newline-separated headlines
    """
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    
    # Try multiple times in case of network issues
    for attempt in range(max_retries):
        try:
            print(f"[NewsFetcher] Attempt {attempt+1}/{max_retries}: Fetching calendar data...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            # Parse JSON data
            events = response.json()
            return format_calendar_events(events, count)
            
        except requests.exceptions.RequestException as e:
            print(f"[NewsFetcher] Error fetching calendar data (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                delay = 2 ** attempt  # Exponential backoff
                print(f"[NewsFetcher] Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("[NewsFetcher] All attempts failed.")
                return generate_mock_headlines()
        except json.JSONDecodeError as e:
            print(f"[NewsFetcher] Error parsing JSON data: {e}")
            if attempt < max_retries - 1:
                delay = 2 ** attempt
                print(f"[NewsFetcher] Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("[NewsFetcher] All JSON parsing attempts failed.")
                return generate_mock_headlines()

def format_calendar_events(events: List[Dict[str, Any]], count: int) -> str:
    """
    Format calendar events into headline strings with priority for high-impact events.
    
    Args:
        events: List of calendar event dictionaries
        count: Maximum number of headlines to return
    
    Returns:
        String with formatted headlines separated by newlines
    """
    # Sort events: first by impact (High > Medium > Low), then by date (most recent first)
    # Make sure we use a timezone-aware datetime to match the API response
    try:
        # Try to get timezone-aware current time
        now = datetime.datetime.now(datetime.timezone.utc)
    except Exception as e:
        # Fallback to naive datetime if timezone handling fails
        print(f"[NewsFetcher] Warning: Using naive datetime due to error: {e}")
        now = datetime.datetime.now()
    
    # Convert date strings to datetime objects for sorting
    for event in events:
        try:
            # Parse the event date string to datetime
            event_datetime = event['date']
            # Remove the Z and replace with UTC offset for proper parsing
            if event_datetime.endswith('Z'):
                event_datetime = event_datetime[:-1] + '+00:00'
            # Parse the ISO format string to a datetime object
            event['datetime'] = datetime.datetime.fromisoformat(event_datetime)
            # Calculate how close the event is to now
            event['time_proximity'] = abs((event['datetime'] - now).total_seconds())
        except (ValueError, KeyError) as e:
            # If date parsing fails, put it at the end
            print(f"[NewsFetcher] Date parsing error: {e} for event: {event.get('title', 'Unknown')}")
            event['time_proximity'] = float('inf')
    
    # Define impact priority (High=3, Medium=2, Low=1, None=0)
    impact_priority = {"High": 3, "Medium": 2, "Low": 1, "": 0}
    
    # Sort events by impact (highest first), then by proximity to current time
    sorted_events = sorted(
        events,
        key=lambda x: (-impact_priority.get(x.get('impact', ''), 0), x.get('time_proximity', float('inf')))
    )
    
    # Format headlines
    headlines = []
    for event in sorted_events[:count]:
        try:
            # Format date to a readable string
            event_date = event.get('datetime', now).strftime("%Y-%m-%d %H:%M")
            
            # Create a formatted headline
            impact = f"[{event.get('impact', 'Unknown')} Impact]" if event.get('impact') else ""
            currency = f"[{event.get('country', '')}]" if event.get('country') else ""
            title = event.get('title', 'Unknown Event')
            forecast = f"Forecast: {event.get('forecast', 'N/A')}" if event.get('forecast') else ""
            previous = f"Previous: {event.get('previous', 'N/A')}" if event.get('previous') else ""
            
            # Combine components into a headline
            headline_parts = [part for part in [currency, impact, title, forecast, previous] if part]
            headline = f"{event_date} - {' '.join(headline_parts)}"
            
            headlines.append(headline)
            print(f"[NewsFetcher] Formatted headline: {headline}")
            
        except Exception as e:
            print(f"[NewsFetcher] Error formatting event: {e}")
            continue
    
    # If we couldn't get enough headlines from the calendar
    if not headlines:
        return generate_mock_headlines()
    
    print(f"[NewsFetcher] Returning {len(headlines)} formatted headlines")
    return "\n".join(headlines)

def generate_mock_headlines() -> str:
    """
    Generate mock headlines as a fallback when API fails.
    
    Returns:
        String with newline-separated mock headlines
    """
    print("[NewsFetcher] Generating mock headlines due to fetch/parse failure")
    mock_headlines = [
        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} - [USD] [High Impact] FOMC Statement - Rate decision expected",
        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} - [EUR] [Medium Impact] German Factory Orders m/m Forecast: 0.8% Previous: -2.1%",
        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} - [GBP] [High Impact] BOE Inflation Report and Rate Decision",
        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} - [JPY] [Medium Impact] Monetary Policy Statement - Expected to maintain rates",
        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} - [USD] [High Impact] Non-Farm Payrolls Forecast: 180K Previous: 165K"
    ]
    return "\n".join(mock_headlines)
