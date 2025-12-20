import requests
import csv
import io
from datetime import datetime
from .producer import BaseProducer
from .config import TOPICS, NASA_FIRMS_MAP_KEY

FIRMS_URL = (
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/VIIRS_SNPP_NRT/world/1"
)


class FIRMSProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["wildfires"])

    def fetch_and_send(self):
        if not NASA_FIRMS_MAP_KEY:
            return

        url = FIRMS_URL.format(key=NASA_FIRMS_MAP_KEY)
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        reader = csv.DictReader(io.StringIO(resp.text))

        for row in list(reader)[:100]:
            lat = float(row.get("latitude", 0))
            lon = float(row.get("longitude", 0))
            acq_date = row.get("acq_date", "")
            acq_time = row.get("acq_time", "0000")
            frp = float(row.get("frp", 0) or 0)

            try:
                dt = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M")
                timestamp = dt.isoformat() + "Z"
            except ValueError:
                timestamp = datetime.utcnow().isoformat() + "Z"

            event = {
                "event_id": f"firms_{acq_date}_{lat:.3f}_{lon:.3f}",
                "event_type": "wildfire",
                "source": "NASA_FIRMS",
                "timestamp": timestamp,
                "title": f"Fire detected at {lat:.2f}, {lon:.2f}",
                "description": f"FRP: {frp} MW",
                "latitude": lat,
                "longitude": lon,
                "frp": frp,
                "confidence": row.get("confidence"),
                "satellite": row.get("satellite", "VIIRS"),
            }
            self.send(event["event_id"], event)


if __name__ == "__main__":
    FIRMSProducer().fetch_and_send()
