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
        self.consumer = None

    
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
            if not event.get("timestamp"):
                continue  # Skip events without timestamp
            
            event_ids.append(event["event_id"])
            documents.append(event["description"])
            metadata_list.append(
                {
                    "source": event["source"],
                    "timestamp": event["timestamp"],
                    "timestamp_ts": event["timestamp_ts"],
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


    # def run_historical(self) -> None:
    #     """Embed all existing events in the topic"""
    #     logging.info("Starting historical embedding...")

    #     # Create a temporary consumer for historical data
    #     historical_consumer = KafkaConsumer(
    #         TOPIC,
    #         bootstrap_servers=KAFKA_SERVERS,
    #         auto_offset_reset="earliest",
    #         group_id="embedding-group-historical",
    #         value_deserializer=lambda m: json.loads(m.decode()),
    #     )

    #     messages = []
    #     try:
    #         for message in historical_consumer:
    #             messages.append(message)
    #             if len(messages) > 1000:  # Safety limit
    #                 break
    #     except Exception as e:
    #         logging.error(f"Error collecting historical messages: {e}")

    #     logging.info(f"Collected {len(messages)} historical messages")

    #     for message in messages:
    #         try:
    #             event = message.value
    #             self.build_and_store(event)
    #         except Exception as e:
    #             logging.error(f"Error processing historical event: {e}")

    #     historical_consumer.close()
    #     logging.info("Historical embedding completed")

    def run_streaming(self) -> None:
        """Stream and embed new events from the topic, processing in micro-batches"""
        logging.info("Starting streaming consumer for new events...")
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_SERVERS,
            auto_offset_reset="latest",
            group_id="embedding-group",
            value_deserializer=lambda m: json.loads(m.decode()),
        )

        try:
            for message in consumer:
                try:
                    event = message.value
                    logging.info(
                        f"Processing new event: {event.get('event_id', 'unknown')}"
                    )
                    self.build_and_store(event)
                except Exception as e:
                    logging.error(f"Error processing event: {e}")
        except KeyboardInterrupt:
            logging.info("Streaming consumer stopped by user")

    def run_consumer(self) -> None:
        """First embed historical events, then stream new events"""
        # self.run_historical()
        self.run_streaming()


def main():
    """Main function to run the builder consumer"""
    logging.basicConfig(level=logging.INFO)
    builder = Builder()
    builder.run_consumer()


if __name__ == "__main__":
    main()
