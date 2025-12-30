from src.embedding.embedder import Embedder
import numpy as np


def calculate_distance(v1, v2):
    return np.linalg.norm(np.array(v1) - np.array(v2)) ** 2


embedder = Embedder()
query = "is there some disaster in hawaii?"
doc = "Event details Event ID: usgs_hv74865037 Event type: earthquake Source: USGS Timestamp: 2025-12-30 13:22 UTC Ingested at: 2025-12-30T13:30:47.941144Z Title: M 1.9 - 11 km NE of Pāhala, Hawaii"

q_emb = embedder.embed(query)
d_emb = embedder.embed(doc)

dist = calculate_distance(q_emb, d_emb)
print(f"Cosine Distance (L2 squared in Chroma): {dist}")
