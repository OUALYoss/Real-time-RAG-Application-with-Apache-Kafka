import requests
from datetime import datetime
from .producer import BaseProducer
from .config import TOPICS
import logging


class ReliefWebProducer(BaseProducer):
    """Fetches humanitarian disaster reports from ReliefWeb API"""

    def __init__(self):
        super().__init__(TOPICS["disasters"])
        self.api_url = "https://api.reliefweb.int/v1/disasters"

    def fetch_and_send(self):
        """Fetch recent disasters from ReliefWeb"""
        params = {
            "appname": "disaster-rag",
            "profile": "list",
            "preset": "latest",
            "limit": 20,
        }

        try:
            resp = requests.get(self.api_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            disasters = data.get("data", [])
            logging.info(f"ReliefWeb returned {len(disasters)} disasters")

            for item in disasters:
                fields = item.get("fields", {})

                # Extract country info (simplified)
                country = "Unknown"
                if fields.get("country"):
                    countries = fields["country"]
                    if isinstance(countries, list) and countries:
                        country = countries[0].get("name", "Unknown")

                # Get disaster type
                disaster_type = "disaster"
                if fields.get("type"):
                    types = fields["type"]
                    if isinstance(types, list) and types:
                        disaster_type = types[0].get("name", "disaster")

                # Normalize to our schema
                event = {
                    "event_id": f"reliefweb_{item.get('id')}",
                    "event_type": disaster_type.lower().replace(" ", "_"),
                    "source": "ReliefWeb",
                    "timestamp": (
                        fields.get("date", {}).get(
                            "created", datetime.now().astimezone().isoformat()
                        )
                        if isinstance(fields.get("date"), dict)
                        else datetime.now().astimezone().isoformat()
                    ),
                    "title": fields.get("name", "Unnamed disaster"),
                    "description": f"{disaster_type} in {country}",
                    "place": country,
                    "status": fields.get("status", ""),
                    "glide": fields.get("glide", ""),
                    "url": fields.get("url", ""),
                }

                self.send(event["event_id"], event)

        except Exception as e:
            logging.error(f"Error fetching ReliefWeb data: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ReliefWebProducer().fetch_and_send()
