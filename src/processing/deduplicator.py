class Deduplicator:
    def __init__(self):
        self.seen_event_ids = set()
        self.seen_title_source = set()

    def is_duplicate(self, event: dict) -> bool:
        event_id = event.get("event_id")
        title = (event.get("title") or "").strip().lower()
        source = (event.get("source") or "").strip().lower()

        # 1. Duplicate by event_id
        if event_id and event_id in self.seen_event_ids:
            return True

        # 2. Duplicate by (title, source)
        key = (title, source)
        if title and source and key in self.seen_title_source:
            return True

        # Mark as seen
        if event_id:
            self.seen_event_ids.add(event_id)
        if title and source:
            self.seen_title_source.add(key)

        return False
