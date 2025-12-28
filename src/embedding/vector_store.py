import chromadb


class VectorStore:
    def __init__(self, host="localhost", port=8000):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection("disaster_events")

    def add(self, event_id: str, embedding: list, document: str, metadata: dict):
        self.collection.add(
            ids=[event_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
        )

    def search(self, query_embedding: list, n=5, where=None):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
            where=where,
        )

    def count(self) -> int:
        return self.collection.count()
