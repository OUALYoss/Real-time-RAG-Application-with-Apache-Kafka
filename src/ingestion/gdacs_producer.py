import feedparser
from .producer import BaseProducer
from .config import TOPICS

GDACS_URL = "https://gdacs.org/xml/rss.xml"

class GDACSProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["disasters"])
    
    def fetch_and_send(self):
        feed = feedparser.parse(GDACS_URL)
        
        for entry in feed.entries:
            event = {
                "event_id": f"gdacs_{entry.get('gdacs_eventid', '')}",
                "event_type": entry.get("gdacs_eventtype", "disaster"),
                "source": "GDACS",
                "timestamp": entry.get("published", ""),
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "alert_level": entry.get("gdacs_alertlevel", ""),
                "latitude": float(entry.get("geo_lat", 0) or 0),
                "longitude": float(entry.get("geo_long", 0) or 0),
            }
            self.send(event["event_id"], event)

if __name__ == "__main__":
    GDACSProducer().fetch_and_send()
