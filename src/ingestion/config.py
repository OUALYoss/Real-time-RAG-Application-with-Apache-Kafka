import os

from dotenv import load_dotenv

load_dotenv()

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPICS = {
    "earthquakes": "raw-earthquakes",
    "disasters": "raw-disasters",
    "weather": "raw-weather",
    "wildfires": "raw-wildfires",
    "news": "raw-news",
    "trends": "raw-trends",
}

INTERVALS = {
    "earthquakes": 60,
    "disasters": 300,
    "weather_nws": 120,
    "weather_owm": 600,
    "wildfires": 900,
    "news": 300,
    "trends": 3600,
}

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NASA_FIRMS_MAP_KEY = os.getenv("NASA_FIRMS_MAP_KEY", "")
