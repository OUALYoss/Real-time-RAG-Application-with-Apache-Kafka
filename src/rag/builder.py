from ..embedding.embedder import Embedder
from ..embedding.vector_store import VectorStore
from kafka import KafkaConsumer, TopicPartition
from datetime import datetime
import json
import logging
import time
from ..ingestion.config import KAFKA_SERVERS


TOPIC = "processed-events"

class Builder:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()
        self.consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_SERVERS,
            auto_offset_reset="latest",
            group_id="embedding-group",
            value_deserializer=lambda m: json.loads(m.decode()),
        )

    def build_and_store(self, event: dict) -> None:
        """Store a single event in vector store, skip if already exists"""
        event_id = event["event_id"]
        
        # Check if event already exists
        existing = self.store.collection.get(ids=[event_id])
        if existing['ids']:
            logging.info(f"Event {event_id} already embedded, skipping")
            return
        
        embedding = self.embedder.embed(event["description"])
        self.store.add(
            event_id=event_id,
            embedding=embedding,
            document=event["description"],
            metadata={"source": event.get("source", "unknown"), 
                      "ingested_at": event.get("ingested_at", "unknown"),
                      "event_type": event.get("event_type", "unknown"),
                      "url": event.get("url", "unknown")
            }

        )
        logging.info(f"Stored event: {event_id}")

    def run_historical(self) -> None:
        """Embed all existing events in the topic"""
        logging.info("Starting historical embedding...")

        # Create a temporary consumer for historical data
        historical_consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_SERVERS,
            auto_offset_reset="earliest",
            group_id="embedding-group-historical",
            value_deserializer=lambda m: json.loads(m.decode()),
        )

        messages = []
        try:
            for message in historical_consumer:
                messages.append(message)
                if len(messages) > 1000:  # Safety limit
                    break
        except Exception as e:
            logging.error(f"Error collecting historical messages: {e}")

        logging.info(f"Collected {len(messages)} historical messages")

        for message in messages:
            try:
                event = message.value
                self.build_and_store(event)
            except Exception as e:
                logging.error(f"Error processing historical event: {e}")

        historical_consumer.close()
        logging.info("Historical embedding completed")


    def run_streaming(self) -> None:
        """Stream and embed new events from the topic as they arrive, skipping duplicates"""
        logging.info("Starting streaming consumer for new events...")

        try:
            for message in self.consumer:
                try:
                    event = message.value
                    logging.info(f"Processing new event: {event.get('event_id', 'unknown')}")
                    self.build_and_store(event)
                except Exception as e:
                    logging.error(f"Error processing event: {e}")
        except KeyboardInterrupt:
            logging.info("Streaming consumer stopped by user")

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