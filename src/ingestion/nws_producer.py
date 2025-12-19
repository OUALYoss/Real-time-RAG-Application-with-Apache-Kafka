import requests
from .producer import BaseProducer
from .config import TOPICS

NWS_URL = "https://api.weather.gov/alerts/active"

class NWSProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["weather"])
    
    def fetch_and_send(self):
        headers = {"User-Agent": "DisasterRAG/1.0"}
        resp = requests.get(NWS_URL, headers=headers, timeout=30)
        data = resp.json()
        
        for feature in data.get("features", [])[:20]:
            props = feature["properties"]
            event = {
                "event_id": f"nws_{props.get('id', '')}",
                "event_type": "weather_alert",
                "source": "NWS",
                "timestamp": props.get("sent", ""),
                "title": props.get("headline", ""),
                "description": props.get("description", "")[:500],
                "severity": props.get("severity", ""),
                "areas": props.get("areaDesc", ""),
            }
            self.send(event["event_id"], event)

if __name__ == "__main__":
    NWSProducer().fetch_and_send()
