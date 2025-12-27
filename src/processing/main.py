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
            api_version=(2, 8, 1),
            auto_offset_reset="earliest",
            group_id="processing-group-streaming",  # 🔥 NOUVEAU GROUPE
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode()),
            consumer_timeout_ms=10000,  # Timeout after 10 seconds
        )

        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            api_version=(2, 8, 1),
            value_serializer=lambda v: json.dumps(v).encode(),
        )

    def run(self):
        print("Processor checking for messages...")
        try:
            count = 0
            for message in self.consumer:
                try:
                    event = message.value
                    print(f"Processing event: {event.get('id', 'unknown')}")
                    normalized = self.normalizer.normalize(event)

                    if self.deduplicator.is_duplicate(normalized):
                        print("Duplicate skipped")
                        continue

                    self.producer.send(
                        OUTPUT_TOPIC,
                        key=normalized["event_id"].encode(),
                        value=normalized,
                    )
                    self.producer.flush()
                    print(f"Produced event {normalized['event_id']}")
                    count += 1
                except Exception as e:
                    print(f"Error processing message: {e}")
            print(f"Processor finished batch. Processed {count} messages.")
        except Exception as e:
            print(f"Error in processor run: {e}")

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
