import requests
from datetime import datetime
from .producer import BaseProducer
from .config import TOPICS

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"


class USGSProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["earthquakes"])

    def fetch_and_send(self):
        resp = requests.get(USGS_URL, timeout=30)
        resp.raise_for_status()

        for f in resp.json().get("features", []):
            props = f["properties"]
            coords = f["geometry"]["coordinates"]
            event = {
                "event_id": f"usgs_{f['id']}",
                "event_type": "earthquake",
                "source": "USGS",
                "timestamp": datetime.utcfromtimestamp(props["time"] / 1000).isoformat()
                + "Z",
                "latitude": coords[1],
                "longitude": coords[0],
                "depth_km": coords[2],
                "magnitude": props.get("mag"),
                "place": props.get("place"),
                "title": props.get("title"),
                "url": props.get("url"),
            }
            self.send(event["event_id"], event)


if __name__ == "__main__":
    USGSProducer().fetch_and_send()
