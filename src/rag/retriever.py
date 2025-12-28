import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from embedding.embedder import Embedder
from embedding.vector_store import VectorStore
from datetime import datetime, timedelta


class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()

    def retrieve(
        self, query: str, duration_hours: int = 1, n=5, threshold=0.8
    ) -> (
        list
    ):  # For cosine distance, 0.0 is exact match, 1.0 is unrelated. 0.8 is a safe threshold.
        embedding = self.embedder.embed(query)

        where = None
        if duration_hours is not None:
            now_ts = int(datetime.utcnow().timestamp())
            lower_bound = now_ts - duration_hours * 3600
            print("Lower bound timestamp:", lower_bound)

            where = {"timestamp_ts": {"$gte": lower_bound}}

        results = self.store.search(
            embedding,
            n=n,
            where=where, # filtrage AVANT similarité
        )

        events = []
        if results["ids"][0]:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]

                # Filter: only include results below distance threshold (lower distance = higher similarity)
                if distance <= threshold:
                    events.append(
                        {
                            "id": results["ids"][0][i],
                            "document": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": distance,
                            "confidence": max(
                                0, 1 - distance
                            ),  # Convert to confidence score
                        }
                    )
        return events
