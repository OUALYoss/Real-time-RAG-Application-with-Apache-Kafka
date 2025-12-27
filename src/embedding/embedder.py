from sentence_transformers import SentenceTransformer

MODEL = "all-MiniLM-L6-v2"


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(MODEL)

    def embed(self, text: str) -> list:
        # Normalize embeddings for better distance calculations (0.0 to 1.0 range)
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_event(self, event: dict) -> list:
        text = (
            f"{event.get('title', '')} "
            f"{event.get('description', '')} "
            f"{event.get('place', '')}"
        )
        return self.embed(text)
