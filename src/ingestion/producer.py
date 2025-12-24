import json
from kafka import KafkaProducer
from datetime import datetime
from .config import KAFKA_SERVERS
import logging


class BaseProducer:
    def __init__(self, topic: str):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode(),
        )

    def send(self, key: str, data: dict) -> None:
        data["ingested_at"] = datetime.utcnow().isoformat() + "Z"
        self.producer.send(self.topic, key=key.encode(), value=data)
        self.producer.flush()
        logging.info(f"[{self.topic}] Sent: {key}")
