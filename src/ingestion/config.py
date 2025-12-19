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
}
