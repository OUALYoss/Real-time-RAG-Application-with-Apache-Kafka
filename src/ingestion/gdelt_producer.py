import requests
from datetime import datetime
from .producer import BaseProducer
from .config import TOPICS
import logging

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

# Disaster keywords for GDELT query
DISASTER_QUERY = (
    "(earthquake OR flood OR wildfire OR cyclone OR landslide OR "
    "tsunami OR volcano OR hurricane OR tornado OR drought) sourcelang:english"
)


class GDELTProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["trends"])
        self.seen_urls = set()  # Simple dedup cache

    def fetch_and_send(self):
        """Fetch disaster news from GDELT DOC API"""
        params = {
            "query": DISASTER_QUERY,
            "mode": "ArtList",
            "format": "json",
            "timespan": "1h",  # Last hour for good coverage
            "maxrecords": "100",  # Balance freshness vs volume
            "sort": "DateDesc",  # Newest first
        }

        try:
            resp = requests.get(GDELT_DOC_API, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            articles = data.get("articles", [])
            logging.info(f"GDELT returned {len(articles)} articles")

            for article in articles:
                url = article.get("url", "")

                # Skip if we've seen this URL recently
                if url in self.seen_urls:
                    continue

                self.seen_urls.add(url)

                # Keep cache size manageable
                if len(self.seen_urls) > 1000:
                    # Remove oldest half
                    self.seen_urls = set(list(self.seen_urls)[500:])

                # Handle socialimage - can be dict or string
                social_img = article.get("socialimage", "")
                social_caption = ""
                social_url = ""
                if isinstance(social_img, dict):
                    social_caption = social_img.get("caption", "")
                    social_url = social_img.get("url", "")
                elif isinstance(social_img, str):
                    social_url = social_img

                # Normalize to our event schema
                event = {
                    "event_id": f"gdelt_{hash(url) & 0x7FFFFFFF}",
                    "event_type": "news_trend",
                    "source": "GDELT",
                    "timestamp": article.get(
                        "seendate", datetime.now().astimezone().isoformat()
                    ),
                    "title": article.get("title", ""),
                    "description": social_caption or article.get("title", ""),
                    "url": url,
                    "domain": article.get("domain", ""),
                    "language": article.get("language", ""),
                    "social_image": social_url,
                    "tone": article.get("tone"),
                }

                self.send(event["event_id"], event)

        except Exception as e:
            logging.error(f"Error fetching GDELT data: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    GDELTProducer().fetch_and_send()
