import json
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
        self.consumer = KafkaConsumer(
            *RAW_TOPICS,
            bootstrap_servers=KAFKA_SERVERS,
            auto_offset_reset="earliest",
            group_id="processing-group",
            value_deserializer=lambda m: json.loads(m.decode()),
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
    Processor().run()


if __name__ == "__main__":
    main()
