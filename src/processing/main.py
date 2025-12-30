import json
import logging
import signal
from kafka import KafkaConsumer, KafkaProducer
from .normalizer import Normalizer
from .deduplicator import Deduplicator
from ..ingestion.config import KAFKA_SERVERS

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
        self.running = True

    def stop(self, signum, frame):
        logging.info("Stopping processor...")
        self.running = False

    def run(self):
        logging.info("Starting PROCESSING streaming service")

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        try:
            consumer = KafkaConsumer(
                *RAW_TOPICS,
                bootstrap_servers=KAFKA_SERVERS,
                api_version=(2, 8, 1),
                auto_offset_reset="earliest",
                group_id="processing-group-streaming",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode()),
            )

            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVERS,
                api_version=(2, 8, 1),
                value_serializer=lambda v: json.dumps(v).encode(),
            )
        except Exception as e:
            logging.error(f"Failed to initialize Kafka: {e}")
            return

        try:
            while self.running:
                # Poll for messages
                msg_pack = consumer.poll(timeout_ms=1000)
                for tp, messages in msg_pack.items():
                    for message in messages:
                        try:
                            event = message.value
                            normalized = self.normalizer.normalize(event)

                            if self.deduplicator.is_duplicate(normalized):
                                continue

                            producer.send(
                                OUTPUT_TOPIC,
                                key=normalized["event_id"].encode(),
                                value=normalized,
                            )
                            logging.info(
                                f"Processed and sent event: {normalized['event_id']}"
                            )
                        except Exception as e:
                            logging.error(f"Error processing message: {e}")

                producer.flush()
        except Exception as e:
            logging.error(f"Error in processor loop: {e}")
        finally:
            consumer.close()
            producer.close()
            logging.info("Processor cleanup complete.")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] PROCESSING: %(message)s",
    )
    Processor().run()


if __name__ == "__main__":
    main()
