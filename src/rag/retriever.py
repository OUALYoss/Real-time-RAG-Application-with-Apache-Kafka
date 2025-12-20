from ..embedding.embedder import Embedder
from ..embedding.vector_store import VectorStore


class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()

    def retrieve(self, query: str, n=5) -> list:
        embedding = self.embedder.embed(query)
        results = self.store.search(embedding, n=n)

        events = []
        if results["ids"][0]:
            for i in range(len(results["ids"][0])):
                events.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                    }
                )
        return events
