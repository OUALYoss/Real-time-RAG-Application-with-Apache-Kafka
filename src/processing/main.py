import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from .normalizer import Normalizer
from .deduplicator import Deduplicator

KAFKA_SERVERS = "localhost:9092"

RAW_TOPICS = [
    "raw-earthquakes",
    "raw-disasters",
    "raw-weather",
    "raw-wildfires",
    "raw-news",
]

OUTPUT_TOPIC = "processed-events"


class Processor:
    def __init__(self):
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()

    def run(self):
        logging.info("Starting PROCESSING streaming service")

        consumer = KafkaConsumer(
            *RAW_TOPICS,
            bootstrap_servers=KAFKA_SERVERS,
            auto_offset_reset="earliest",
            group_id="processing-group-streaming",  # 🔥 NOUVEAU GROUPE
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode()),
        )

        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode(),
        )

        try:
            for message in consumer:
                event = message.value
                logging.info(
                    f"Processing event {event.get('event_id', 'unknown')}"
                )

                normalized = self.normalizer.normalize(event)

                if self.deduplicator.is_duplicate(normalized):
                    logging.info("Duplicate skipped")
                    continue

                producer.send(
                    OUTPUT_TOPIC,
                    key=normalized["event_id"].encode(),
                    value=normalized,
                )

                logging.info(
                    f"Sent processed event {normalized['event_id']} to {OUTPUT_TOPIC}"
                )

        except KeyboardInterrupt:
            logging.info("Processing stopped by user")

        finally:
            consumer.close()
            producer.close()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[PROCESSING] %(levelname)s - %(message)s",
    )

    Processor().run()


if __name__ == "__main__":
    main()