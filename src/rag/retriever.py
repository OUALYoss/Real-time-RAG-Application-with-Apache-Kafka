from ..embedding.embedder import Embedder
from ..embedding.vector_store import VectorStore


class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()

    def retrieve(
        self, query: str, n=5, threshold=0.8
    ) -> (
        list
    ):  # For cosine distance, 0.0 is exact match, 1.0 is unrelated. 0.8 is a safe threshold.
        embedding = self.embedder.embed(query)
        results = self.store.search(embedding, n=n)

        events = []
        if results["ids"][0]:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]

                # Filter: only include results below distance threshold
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
