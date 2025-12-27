import requests
from datetime import datetime
from .producer import BaseProducer
from .config import TOPICS
import logging


class EONETProducer(BaseProducer):
    """Fetches natural events from NASA EONET API"""

    def __init__(self):
        super().__init__(TOPICS["disasters"])
        self.api_url = "https://eonet.gsfc.nasa.gov/api/v3/events"
        self.categories = "wildfires,severeStorms,floods,volcanoes,landslides"

    def fetch_and_send(self):
        """Fetch recent natural events from NASA EONET"""
        params = {
            "category": self.categories,
            "days": 14,  # Last 2 weeks
            "status": "open",
            "limit": 100,
        }

        try:
            resp = requests.get(self.api_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            events = data.get("events", [])
            logging.info(f"NASA EONET returned {len(events)} events")

            for item in events:
                # Extract category
                categories = item.get("categories", [{}])
                category = (
                    categories[0].get("title", "Natural Event")
                    if categories
                    else "Natural Event"
                )

                # Extract location from first geometry
                geometries = item.get("geometry", item.get("geometries", []))
                place = "Unknown location"
                if geometries:
                    geo = geometries[0]
                    coords = geo.get("coordinates", [])
                    if len(coords) >= 2:
                        place = f"{coords[1]:.2f}°N, {coords[0]:.2f}°E"

                # Get date
                event_date = (
                    geometries[0].get("date")
                    if geometries
                    else item.get("geometry", [{}])[0].get("date", "")
                )
                if not event_date:
                    event_date = datetime.utcnow().isoformat() + "Z"

                # Normalize to our schema
                event = {
                    "event_id": f"eonet_{item.get('id')}",
                    "event_type": category.lower().replace(" ", "_"),
                    "source": "NASA_EONET",
                    "timestamp": event_date,
                    "title": item.get("title", "Unnamed event"),
                    "description": (
                        f"Category: {category}. Source: {item.get('sources', [{}])[0].get('id', 'satellite')}"
                        if item.get("sources")
                        else f"Category: {category}"
                    ),
                    "place": place,
                    "link": item.get("link", ""),
                    "closed": item.get("closed"),
                }

                self.send(event["event_id"], event)

        except Exception as e:
            logging.error(f"Error fetching NASA EONET data: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    EONETProducer().fetch_and_send()
