import requests
from datetime import datetime
from .producer import BaseProducer
from .config import TOPICS, NEWS_API_KEY

NEWS_URL = "https://api.thenewsapi.com/v1/news/all"
KEYWORDS = "earthquake OR tsunami OR hurricane OR wildfire OR flood OR disaster"


class NewsProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["news"])

    def fetch_and_send(self):
        if not NEWS_API_KEY:
            return

        params = {
            "api_token": NEWS_API_KEY,
            "search": KEYWORDS,
            "language": "en",
            "limit": 20,
        }
        resp = requests.get(NEWS_URL, params=params, timeout=30)
        resp.raise_for_status()

        for article in resp.json().get("data", []):
            event = {
                "event_id": f"news_{article.get('uuid', '')}",
                "event_type": "news",
                "source": article.get("source", "TheNewsAPI"),
                "timestamp": article.get(
                    "published_at", datetime.utcnow().isoformat() + "Z"
                ),
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "snippet": article.get("snippet", ""),
                "url": article.get("url", ""),
                "image_url": article.get("image_url", ""),
            }
            self.send(event["event_id"], event)


if __name__ == "__main__":
    NewsProducer().fetch_and_send()
