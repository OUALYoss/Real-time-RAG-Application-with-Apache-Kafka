class Normalizer:
    def normalize(self, event: dict) -> dict:
        return {
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type", "unknown"),
            "source": event.get("source", "unknown"),
            "timestamp": event.get("timestamp"),
            "ingested_at": event.get("ingested_at"),
            "title": event.get("title", ""),
            "description": event.get("description", ""),
            "latitude": event.get("latitude"),
            "longitude": event.get("longitude"),
            "severity": self._get_severity(event),
            "metadata": self._get_metadata(event),
        }

    def _get_severity(self, event: dict) -> str:
        source = event.get("source", "")

        if source == "USGS":
            mag = event.get("magnitude", 0) or 0
            if mag >= 6:
                return "high"
            elif mag >= 4:
                return "medium"
            return "low"

        if source == "GDACS":
            level = event.get("alert_level", "").lower()
            return {"red": "high", "orange": "medium", "green": "low"}.get(level, "low")

        if source == "NASA_FIRMS":
            frp = event.get("frp", 0) or 0
            if frp >= 50:
                return "high"
            elif frp >= 20:
                return "medium"
            return "low"

        if source == "NWS":
            sev = event.get("severity", "").lower()
            if sev in ["extreme", "severe"]:
                return "high"
            elif sev == "moderate":
                return "medium"
            return "low"

        return "low"
