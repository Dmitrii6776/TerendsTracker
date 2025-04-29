# 🚀 Crypto Sentiment + Trend Tracker with Volatility Zones (Advanced)

import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import json
from datetime import datetime
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# --- Data Holder ---
sentiment_data = {}

# --- Configuration ---
COINGECKO_TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"
FEAR_GREED_URL = "https://api.alternative.me/fng/"
REDDIT_URL = "https://www.reddit.com/r/CryptoCurrency/top/?t=day"
USER_AGENT = {"User-Agent": "Mozilla/5.0"}

# Dummy prices for demonstration (replace with Bybit API integration)
DUMMY_MARKET_DATA = {
    "SOL": {"last": 132.45, "high": 137, "low": 126},
    "DOGE": {"last": 0.134, "high": 0.145, "low": 0.128},
    "PEPE": {"last": 0.00000127, "high": 0.0000015, "low": 0.0000011}
}

# --- Volatility Strategy Zones ---
def determine_volatility_zone(volatility):
    if volatility <= 3:
        return "Very Low Volatility", "Micro Scalping Strategy"
    elif volatility <= 7:
        return "Low Volatility", "Short-Term Tight Strategy"
    elif volatility <= 12:
        return "Medium Volatility", "Balanced Normal Strategy"
    elif volatility <= 18:
        return "High Volatility", "Flexible Swing Strategy"
    else:
        return "Very High Volatility", "Big Swing Survival Strategy"

# --- Sentiment Update Function ---
def fetch_trending_coins():
    response = requests.get(COINGECKO_TRENDING_URL)
    data = response.json()
    trending = [coin['item']['symbol'].upper() for coin in data['coins']]
    return trending

def fetch_fear_greed_index():
    response = requests.get(FEAR_GREED_URL)
    data = response.json()
    score = data['data'][0]['value']
    classification = data['data'][0]['value_classification']
    return int(score), classification

def fetch_reddit_mentions(trending_coins):
    response = requests.get(REDDIT_URL, headers=USER_AGENT)
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('h3')
    text_content = ' '.join(post.get_text() for post in posts)
    mentions = Counter()
    for symbol in trending_coins:
        pattern = r'\b' + re.escape(symbol) + r'\b'
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        mentions[symbol] = len(matches)
    return mentions

def update_sentiment_data():
    global sentiment_data
    print(f"[{datetime.now()}] Updating sentiment data...")
    try:
        trending_coins = fetch_trending_coins()
        fear_greed_score, fear_greed_class = fetch_fear_greed_index()
        reddit_mentions = fetch_reddit_mentions(trending_coins)

        sentiment_data = {
            "timestamp": datetime.now().isoformat(),
            "fear_greed": {
                "score": fear_greed_score,
                "classification": fear_greed_class
            },
            "trending_coins": []
        }

        for coin in trending_coins:
            market = DUMMY_MARKET_DATA.get(coin, None)
            if not market:
                continue  # Skip if we don't have data

            last_price = market['last']
            high_24h = market['high']
            low_24h = market['low']

            volatility = (high_24h - low_24h) / last_price * 100
            zone, strategy = determine_volatility_zone(volatility)

            mentions = reddit_mentions.get(coin, 0)
            signal = "BUY" if mentions >= 2 and fear_greed_score >= 50 else "CAUTION"

            sentiment_data["trending_coins"].append({
                "symbol": coin,
                "reddit_mentions": mentions,
                "signal": signal,
                "volatility_percent": round(volatility, 2),
                "volatility_zone": zone,
                "strategy_description": strategy
            })

        print(f"[{datetime.now()}] Sentiment data updated successfully.")

    except Exception as e:
        print(f"Error updating sentiment data: {e}")

# --- Flask API ---
@app.route("/")
def root():
    return "Crypto Sentiment Trends API is running 🚀"

@app.route("/sentiment", methods=["GET"])
def get_sentiment_data():
    return jsonify(sentiment_data)

# --- Main Execution ---
if __name__ == "__main__":
    update_sentiment_data()
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_sentiment_data, "interval", minutes=30)
    scheduler.start()
    app.run(host="0.0.0.0", port=8000)
