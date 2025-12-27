import json
from apscheduler.schedulers.blocking import BlockingScheduler
from kafka import KafkaConsumer, KafkaProducer
from .normalizer import Normalizer
from .deduplicator import Deduplicator

KAFKA_SERVERS = "127.0.0.1:9094"
RAW_TOPICS = [
    "raw-earthquakes",
    "raw-disasters",
    "raw-weather",
    "raw-wildfires",
    "raw-news",
]
OUTPUT_TOPIC = "processed-events"
PROCESSING_INTERVAL = 60  # Process every 60 seconds


class Processor:
    def __init__(self):
        self.consumer = KafkaConsumer(
            *RAW_TOPICS,
            bootstrap_servers=KAFKA_SERVERS,
            api_version=(2, 8, 1),
            auto_offset_reset="earliest",
            group_id="processing-group",
            value_deserializer=lambda m: json.loads(m.decode()),
            consumer_timeout_ms=10000,  # Timeout after 10 seconds
        )
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            api_version=(2, 8, 1),
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()

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


def main():
    """Main function with scheduler"""
    processor = Processor()

    # Process immediately at startup
    print("Processing initial batch...")
    processor.run()

    # Set up scheduler for periodic processing
    scheduler = BlockingScheduler()
    scheduler.add_job(
        processor.run, "interval", seconds=PROCESSING_INTERVAL, id="batch_processing"
    )

    print(f"Starting scheduled processing every {PROCESSING_INTERVAL} seconds...")
    scheduler.start()


if __name__ == "__main__":
    main()
