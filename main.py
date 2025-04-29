import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import json
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# --- Data Holder ---
sentiment_data = {}

# --- Configuration ---
COINGECKO_TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"
FEAR_GREED_URL = "https://api.alternative.me/fng/"
REDDIT_URL = "https://www.reddit.com/r/CryptoCurrency/top/?t=day"
USER_AGENT = {"User-Agent": "Mozilla/5.0"}

# --- Functions ---
def fetch_trending_coins():
    response = requests.get(COINGECKO_TRENDING_URL)
    data = response.json()
    trending = [coin['item']['symbol'] for coin in data['coins']]
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
        pattern = r'\\b' + re.escape(symbol) + r'\\b'
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        mentions[symbol] = len(matches)
    return mentions

def update_sentiment_data():
    global sentiment_data
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
        mentions = reddit_mentions.get(coin, 0)
        signal = "BUY" if mentions >= 2 and fear_greed_score >= 50 else "CAUTION"
        sentiment_data["trending_coins"].append({
            "symbol": coin,
            "reddit_mentions": mentions,
            "signal": signal
        })

@app.route("/")
def root():
    return "Crypto Sentiment Trends API is running 🚀"

@app.route("/sentiment", methods=["GET"])
def get_sentiment_data():
    return jsonify(sentiment_data)

if __name__ == "__main__":
    update_sentiment_data()
    app.run(host="0.0.0.0", port=8000)
