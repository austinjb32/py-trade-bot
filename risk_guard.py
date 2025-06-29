# risk_guard.py

from together import Together
import config

# Initialize Together client
client = Together(api_key=config.TOGETHER_API_KEY)

def check_news_risk():
    # Ideally replace with scraped news or API feed
    latest_news = "US Fed to announce rate decision today."
    prompt = f"""
    Headlines: {latest_news}
    Should I CLOSE all EUR/USD trades now due to risk? Answer 'YES' or 'NO'.
    """
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return "YES" in response.choices[0].message.content.upper()
