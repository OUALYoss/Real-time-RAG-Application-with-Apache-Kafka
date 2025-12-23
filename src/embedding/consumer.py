import json
from kafka import KafkaConsumer
from .embedder import Embedder
from .vector_store import VectorStore

KAFKA_SERVERS = "localhost:9092"
TOPIC = "processed-events"


class EmbeddingConsumer:
    def __init__(self):
        self.consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_SERVERS,
            auto_offset_reset="earliest",
            group_id="embedding-group",
            value_deserializer=lambda m: json.loads(m.decode()),
        )
        self.embedder = Embedder()
        self.store = VectorStore()

    def run(self):
        for message in self.consumer:
            event = message.value

            text = f"{event.get('title', '')} {event.get('description', '')}"
            embedding = self.embedder.embed(text)

            metadata = {
                "event_type": event.get("event_type", ""),
                "source": event.get("source", ""),
                "timestamp": event.get("timestamp", ""),
                "severity": event.get("severity", ""),
            }

            self.store.add(
                event_id=event.get("event_id"),
                embedding=embedding,
                document=text,
                metadata=metadata,
            )


def main():
    EmbeddingConsumer().run()


if __name__ == "__main__":
    main()
