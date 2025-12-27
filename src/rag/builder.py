from ..embedding.embedder import Embedder
from ..embedding.vector_store import VectorStore
import json
import logging
from kafka import KafkaConsumer
from ..ingestion.config import KAFKA_SERVERS


TOPIC = "processed-events"


class Builder:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()
        self.consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_SERVERS,
            api_version=(2, 8, 1),
            auto_offset_reset="latest",
            group_id="embedding-group",
            value_deserializer=lambda m: json.loads(m.decode()),
        )

    def _synthesize_document(self, event: dict) -> str:
        """Create a natural language document from event data"""
        et = event.get("event_type", "Disaster").replace("_", " ").title()
        title = event.get("title") or f"{et} event"
        desc = event.get("description") or ""
        place = event.get("place") or ""
        timestamp = event.get("timestamp", "")

        # Format timestamp to standard format if available
        time_str = ""
        if timestamp:
            try:
                # Extract just the date and time portion (YYYY-MM-DD HH:MM)
                if "T" in timestamp:
                    time_str = (
                        timestamp.split("T")[0]
                        + " "
                        + timestamp.split("T")[1][:5]
                        + " UTC"
                    )
                else:
                    time_str = (
                        timestamp[:16] + " UTC" if len(timestamp) >= 16 else timestamp
                    )
            except:
                time_str = timestamp

        # Natural language format for better embedding
        # We put the event type and place first to boost their relevance
        parts = []
        parts.append(
            f"{et} in {place if place and place != 'N/A' else 'Unknown Location'}"
        )

        if (
            title
            and title != "Unknown event"
            and title.lower() not in (place.lower() if place else "")
        ):
            parts.append(title)

        if time_str:
            parts.append(f"Occurred at {time_str}")

        if desc and desc != "N/A" and len(desc) > 5:
            # Only add first 100 chars of desc to keep it dense
            parts.append(desc[:150] + ("..." if len(desc) > 150 else ""))

        return ". ".join(parts) + "." if parts else "Disaster event."

    def build_and_store_batch(self, events: list) -> None:
        """Process and store a batch of events efficiently"""
        if not events:
            return

        # Prepare batch data
        event_ids = []
        documents = []
        metadata_list = []
        embed_inputs = []

        for event in events:
            event_ids.append(event["event_id"])
            documents.append(self._synthesize_document(event))
            metadata_list.append(
                {
                    "source": event["source"],
                    "timestamp": event["timestamp"],
                    "event_type": event["event_type"],
                    "title": event.get("title", ""),
                    "place": event.get("place", ""),
                }
            )
            # Prepare for embedding using the embedder's logic
            embed_inputs.append(
                {
                    "title": event.get("title", ""),
                    "description": event.get("description", ""),
                    "place": event.get("place", ""),
                }
            )

        # Batch embed the actual natural language documents
        embeddings = self.embedder.model.encode(
            documents, normalize_embeddings=True
        ).tolist()

        # Batch upsert to ChromaDB - single transaction
        self.store.collection.upsert(
            ids=event_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadata_list,
        )
        logging.info(f"Stored batch of {len(events)} events")

    def build_and_store(self, event: dict) -> None:
        """Store a single event - wraps batch method for compatibility"""
        self.build_and_store_batch([event])

    def run_historical(self) -> None:
        """Embed all existing events in the topic"""
        logging.info("Starting historical embedding...")

        # Create a temporary consumer for historical data
        historical_consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_SERVERS,
            api_version=(2, 8, 1),
            auto_offset_reset="earliest",
            group_id="embedding-group-historical",
            value_deserializer=lambda m: json.loads(m.decode()),
            consumer_timeout_ms=5000,
        )

        messages = []
        try:
            for message in historical_consumer:
                messages.append(message.value)
                if len(messages) > 1000:  # Safety limit
                    break
        except Exception as e:
            logging.error(f"Error collecting historical messages: {e}")

        logging.info(f"Collected {len(messages)} historical messages")

        # Process in batches for efficiency
        batch_size = 20
        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            try:
                self.build_and_store_batch(batch)
            except Exception as e:
                logging.error(f"Error processing historical batch: {e}")

        historical_consumer.close()
        logging.info("Historical embedding completed")

    def run_streaming(self) -> None:
        """Stream and embed new events from the topic, processing in micro-batches"""
        logging.info("Starting streaming consumer for new events...")

        while True:
            batch = []
            batch_size = 10  # Process 10 events at a time

            try:
                for message in self.consumer:
                    try:
                        event = message.value
                        batch.append(event)

                        # Process when batch is full
                        if len(batch) >= batch_size:
                            self.build_and_store_batch(batch)
                            batch = []
                    except Exception as e:
                        logging.error(f"Error adding event to batch: {e}")

                # Process any remaining events if the loop breaks normally
                if batch:
                    self.build_and_store_batch(batch)
            except Exception as e:
                logging.error(
                    f"Streaming consumer encountered an error: {e}. Restarting in 5s..."
                )
                import time

                time.sleep(5)
                # Re-initialize consumer if needed?
                # The kafka-python consumer usually handles reconnects,
                # but if the iterator breaks, we might need a fresh start.
                continue
            except KeyboardInterrupt:
                if batch:
                    self.build_and_store_batch(batch)
                logging.info("Streaming consumer stopped by user")
                break

    def run_consumer(self) -> None:
        """First embed historical events, then stream new events"""
        self.run_historical()
        self.run_streaming()


def main():
    """Main function to run the builder consumer"""
    logging.basicConfig(level=logging.INFO)
    builder = Builder()
    builder.run_consumer()


if __name__ == "__main__":
    main()
