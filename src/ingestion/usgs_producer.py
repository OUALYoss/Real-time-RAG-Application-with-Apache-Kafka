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
        data = resp.json()

        for feature in data.get("features", []):
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]

            event = {
                "event_id": f"usgs_{feature['id']}",
                "event_type": "earthquake",
                "source": "USGS",
                "timestamp": datetime.utcfromtimestamp(props["time"] / 1000).isoformat()
                + "Z",
                "latitude": coords[1],
                "longitude": coords[0],
                "magnitude": props.get("mag"),
                "place": props.get("place"),
                "title": props.get("title"),
            }
            self.send(event["event_id"], event)


if __name__ == "__main__":
    USGSProducer().fetch_and_send()
