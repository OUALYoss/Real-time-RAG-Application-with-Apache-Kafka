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
        resp.raise_for_status()

        for f in resp.json().get("features", [])[:50]:
            props = f["properties"]
            event = {
                "event_id": f"nws_{props.get('id', '')}",
                "event_type": "weather_alert",
                "source": "NWS",
                "timestamp": props.get("sent", ""),
                "title": props.get("headline", ""),
                "description": (props.get("description") or "")[:1000],
                "severity": props.get("severity", ""),
                "urgency": props.get("urgency", ""),
                "event": props.get("event", ""),
                "areas": props.get("areaDesc", ""),
                "expires": props.get("expires", ""),
            }
            self.send(event["event_id"], event)


if __name__ == "__main__":
    NWSProducer().fetch_and_send()
