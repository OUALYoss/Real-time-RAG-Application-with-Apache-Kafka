from datetime import datetime
import re

class Normalizer:
    def normalize(self, event: dict) -> dict:
        event_normalized = {
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type", "unknown"),
            "source": event.get("source", "unknown"),
            "timestamp": self._format_time(event),
            "ingested_at": event.get("ingested_at"),
            "title": self._format_title(event),
            # "description": self._format_place(event),
            # "latitude": event.get("latitude"),
            # "longitude": event.get("longitude"),
            "place": self._format_place(event),
            "severity": self._get_severity(event),
        }
        event_normalized["description"] = self._format_description(event_normalized, event)
        event_normalized["timestamp_ts"] = self._to_timestamp_ts(event_normalized)
        return event_normalized

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
    

    def _format_time(self, event: dict) -> str | None:
        ts = event.get("timestamp")

        if not ts:
            return None

        ts = str(ts).strip()

        # --- Reject obviously broken timestamps ---
        # Examples: "hu, 1 UTC", "ue, 2 UTC"
        if len(ts) < 10 or re.match(r"^[a-z]{1,3},\s*\d+\s*UTC$", ts, re.IGNORECASE):
            return None

        # --- Case 1: ISO / semi-ISO formats ---
        # 2025-12-27T16:41:32Z
        # 2025-12-27 17:46 UTC
        try:
            if "T" in ts:
                dt = datetime.fromisoformat(
                    ts.replace("Z", "").replace("UTC", "").strip()
                )
                return dt.strftime("%Y-%m-%d %H:%M UTC")

            if re.match(r"\d{4}-\d{2}-\d{2}", ts):
                dt = datetime.fromisoformat(
                    ts.replace("UTC", "").strip()
                )
                return dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            pass

        # --- Case 2: RFC 822 / RFC 1123 with GMT ---
        # Example: Mon, 15 Dec 2025 16:04:04 GMT
        try:
            dt = datetime.strptime(ts, "%a, %d %b %Y %H:%M:%S GMT")
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            pass

        # --- Case 3: RFC 822 with GM (legacy typo) ---
        # Example: Sat, 20 Dec 2025 12:11:22 GM
        try:
            dt = datetime.strptime(ts.replace("GM", "GMT"), "%a, %d %b %Y %H:%M:%S GMT")
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            pass

        # --- Fallback: give up ---
        return None
    


    def _to_timestamp_ts(self, event) -> int | None:
        timestamp_str = event.get("timestamp")
        try:
            dt = datetime.strptime(
                timestamp_str.replace(" UTC", ""),
                "%Y-%m-%d %H:%M"
            )
            return int(dt.timestamp())
        except Exception:
            return None
        



    def _format_place(self, event: dict) -> str:
        place = event.get("place")

        if place and place != "N/A":
            return place

        lat = event.get("latitude")
        lon = event.get("longitude")

        if lat is not None and lon is not None:
            return f"latitude = {lat} and longitude = {lon}"

        return "Unknown Location"
    

    def _format_title(self, event: dict) -> str | None:
        et = event.get("event_type", "Disaster").replace("_", " ").title()
        title = event.get("title") or f"{et} event"
        return title
        

    def _format_description(self, event_normalized: dict, event: dict) -> str:
        """
        Build a final textual description for embedding.
        Priority:
        1) Use raw description from `event` if valid (>5 chars)
        - truncate to 1000 chars if needed
        2) Otherwise synthesize description from `event_normalized`
        In all cases, enrich with structured normalized context.
        """

        parts = []

        # --- 1) Base description from raw event (if usable) ---
        raw_desc = event.get("description")

        if raw_desc and raw_desc != "N/A" and len(raw_desc.strip()) > 5:
            base_desc = raw_desc.strip()
            if len(base_desc) > 1000:
                base_desc = base_desc[:1000] + "..."
            parts.append(base_desc)
        else:
            parts.append("Event details")

        # --- 2) Enrich with normalized structured context ---
        if event_normalized.get("event_id"):
            parts.append(f"Event ID: {event_normalized['event_id']}")

        parts.append(
            f"Event type: {event_normalized.get('event_type', 'unknown')}"
        )
        parts.append(
            f"Source: {event_normalized.get('source', 'unknown')}"
        )

        if event_normalized.get("timestamp"):
            parts.append(f"Timestamp: {event_normalized['timestamp']}")

        if event_normalized.get("ingested_at"):
            parts.append(f"Ingested at: {event_normalized['ingested_at']}")

        if event_normalized.get("title"):
            parts.append(f"Title: {event_normalized['title']}")

        if event_normalized.get("place"):
            parts.append(f"Place: {event_normalized['place']}")

        if event_normalized.get("severity"):
            parts.append(f"Severity: {event_normalized['severity']}")

        return " ".join(parts) + "."


    # def _synthesize_document(self, event: dict) -> str:
    #     """Create a natural language document from event data"""
    #     et = event.get("event_type", "Disaster").replace("_", " ").title()
    #     title = event.get("title") or f"{et} event"
    #     desc = event.get("description") or ""
    #     place = event.get("place") or ""
    #     timestamp = event.get("timestamp", "")

    #     # Natural language format for better embedding
    #     # We put the event type and place first to boost their relevance
    #     parts = []
    #     parts.append(
    #         f"{et} in {place if place and place != 'N/A' else 'Unknown Location'}"
    #     )

    #     if (
    #         title
    #         and title != "Unknown event"
    #         and title.lower() not in (place.lower() if place else "")
    #     ):
    #         parts.append(title)

    #     if time_str:
    #         parts.append(f"Occurred at {time_str}")

    #     if desc and desc != "N/A" and len(desc) > 5:
    #         # Only add first 100 chars of desc to keep it dense
    #         parts.append(desc[:150] + ("..." if len(desc) > 150 else ""))

    #     return ". ".join(parts) + "." if parts else "Disaster event."
