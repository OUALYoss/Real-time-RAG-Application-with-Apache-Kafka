import requests
from datetime import datetime
from .producer import BaseProducer
from .config import TOPICS, OPENWEATHER_API_KEY

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"

CITIES = [
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357},
]


class OWMProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["weather"])

    def fetch_and_send(self):
        if not OPENWEATHER_API_KEY:
            return

        for city in CITIES:
            params = {
                "lat": city["lat"],
                "lon": city["lon"],
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            }
            resp = requests.get(OWM_URL, params=params, timeout=10)
            if not resp.ok:
                continue

            data = resp.json()
            weather = data.get("weather", [{}])[0]
            main = data.get("main", {})
            wind = data.get("wind", {})

            event = {
                "event_id": f"owm_{city['name'].lower()}_{int(datetime.utcnow().timestamp())}",
                "event_type": "weather_report",
                "source": "OpenWeatherMap",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "title": f"Weather in {city['name']}: {weather.get('main', '')}",
                "description": weather.get("description", ""),
                "latitude": city["lat"],
                "longitude": city["lon"],
                "city": city["name"],
                "temperature": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "humidity": main.get("humidity"),
                "wind_speed": wind.get("speed"),
            }
            self.send(event["event_id"], event)


if __name__ == "__main__":
    OWMProducer().fetch_and_send()
