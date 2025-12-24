import json
from apscheduler.schedulers.blocking import BlockingScheduler
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
PROCESSING_INTERVAL = 60  # Process every 60 seconds


class Processor:
    def __init__(self):
        self.consumer = KafkaConsumer(
            *RAW_TOPICS,
            bootstrap_servers=KAFKA_SERVERS,
            auto_offset_reset="earliest",
            group_id="processing-group",
            value_deserializer=lambda m: json.loads(m.decode()),
            consumer_timeout_ms=1000,  # Timeout after 1 second if no messages
        )
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()

    def run(self):
        for message in self.consumer:
            event = message.value
            normalized = self.normalizer.normalize(event)

            if self.deduplicator.is_duplicate(normalized):
                continue

            self.producer.send(
                OUTPUT_TOPIC, key=normalized["event_id"].encode(), value=normalized
            )
            self.producer.flush()


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
    