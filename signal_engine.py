# signal_engine.py

from together import Together
import config

# Initialize Together client
client = Together(api_key=config.TOGETHER_API_KEY)

def get_trade_signal():
    prompt = "Should I BUY or SELL EUR/USD now? Answer with 'BUY', 'SELL', or 'NO TRADE'."
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.upper()
