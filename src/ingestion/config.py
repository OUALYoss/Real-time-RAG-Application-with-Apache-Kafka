import os

from dotenv import load_dotenv

load_dotenv()

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9094")
TOPICS = {
    "earthquakes": "raw-earthquakes",
    "disasters": "raw-disasters",
    "weather": "raw-weather",
    "wildfires": "raw-wildfires",
    "news": "raw-news",
    "trends": "raw-trends",
}

INTERVALS = {
    "earthquakes": 180,  # 3 minutes
    "disasters": 180,  # 3 minutes
    "weather_nws": 180,  # 3 minutes
    "weather_owm": 180,  # 3 minutes
    "wildfires": 180,  # 3 minutes
    "news": 180,  # 3 minutes
    "trends": 180,  # 3 minutes
    "gdelt": 180,  # 3 minutes
    "reliefweb": 180,  # 3 minutes
    "eonet": 180,  # 3 minutes
}

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NASA_FIRMS_MAP_KEY = os.getenv("NASA_FIRMS_MAP_KEY", "")
