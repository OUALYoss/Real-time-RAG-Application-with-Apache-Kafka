import requests
from datetime import datetime
import logging


class OnDemandFetcher:
    """Fetches fresh data from key APIs on-demand for real-time queries"""

    def __init__(self):
        self.sources = {
            "usgs": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
            "gdelt": "https://api.gdeltproject.org/api/v2/doc/doc",
            "eonet": "https://eonet.gsfc.nasa.gov/api/v3/events",
        }

    def fetch_fresh_data(self, query_keywords: list = None) -> list:
        """
        Fetch fresh data from multiple sources
        Returns list of normalized events
        """
        events = []

        # Fetch USGS earthquakes
        try:
            resp = requests.get(self.sources["usgs"], timeout=10)
            resp.raise_for_status()
            data = resp.json()

            for feature in data.get("features", [])[:10]:  # Top 10 recent
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [0, 0, 0])

                events.append(
                    {
                        "event_id": f"fresh_usgs_{props.get('ids', feature.get('id'))}",
                        "source": "USGS",
                        "event_type": "earthquake",
                        "title": props.get("title", "Earthquake"),
                        "timestamp": (
                            datetime.fromtimestamp(
                                props.get("time", 0) / 1000
                            ).isoformat()
                            + "Z"
                            if props.get("time")
                            else datetime.now().isoformat() + "Z"
                        ),
                        "magnitude": props.get("mag"),
                        "place": props.get("place", "Unknown"),
                        "latitude": coords[1],
                        "longitude": coords[0],
                        "description": f"Magnitude {props.get('mag')} earthquake",
                    }
                )
            logging.info(f"Fetched {len(events)} fresh USGS earthquakes")
        except Exception as e:
            logging.error(f"Error fetching fresh USGS data: {e}")

        # Fetch GDELT news (if keywords provided)
        if query_keywords:
            try:
                query = " OR ".join(query_keywords) + " sourcelang:english"
                params = {
                    "query": query,
                    "mode": "ArtList",
                    "format": "json",
                    "timespan": "1h",
                    "maxrecords": "10",
                    "sort": "DateDesc",
                }
                resp = requests.get(self.sources["gdelt"], params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                for article in data.get("articles", [])[:5]:
                    events.append(
                        {
                            "event_id": f"fresh_gdelt_{hash(article.get('url', '')) & 0x7FFFFFFF}",
                            "source": "GDELT",
                            "event_type": "news",
                            "title": article.get("title", "News article"),
                            "timestamp": article.get(
                                "seendate", datetime.now().isoformat()
                            ),
                            "url": article.get("url", ""),
                            "domain": article.get("domain", ""),
                        }
                    )
                logging.info(
                    f"Fetched {len(data.get('articles', [])[:5])} fresh GDELT articles"
                )
            except Exception as e:
                logging.error(f"Error fetching fresh GDELT data: {e}")

        # Fetch NASA EONET events
        try:
            params = {"days": 7, "status": "open", "limit": 10}
            resp = requests.get(self.sources["eonet"], params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("events", [])[:5]:
                categories = item.get("categories", [{}])
                category = (
                    categories[0].get("title", "Natural Event")
                    if categories
                    else "Natural Event"
                )

                events.append(
                    {
                        "event_id": f"fresh_eonet_{item.get('id')}",
                        "source": "NASA_EONET",
                        "event_type": category.lower().replace(" ", "_"),
                        "title": item.get("title", "Natural event"),
                        "timestamp": (
                            item.get("geometries", [{}])[0].get(
                                "date", datetime.now().isoformat()
                            )
                            if item.get("geometries")
                            else datetime.now().isoformat()
                        ),
                    }
                )
            logging.info(
                f"Fetched {len(data.get('events', [])[:5])} fresh EONET events"
            )
        except Exception as e:
            logging.error(f"Error fetching fresh EONET data: {e}")

        return events
