from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ..rag.retriever import Retriever
from ..rag.generator import Generator
from ..rag.news_enricher import NewsEnricher
from ..rag.on_demand_fetcher import OnDemandFetcher
from ..embedding.vector_store import VectorStore
from ..embedding.embedder import Embedder
import uvicorn


app = FastAPI(title="Disaster RAG API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


from ..rag.builder import Builder

retriever = Retriever()
generator = Generator()
enricher = NewsEnricher(max_articles=3)
fetcher = OnDemandFetcher()
embedder = Embedder()
store = VectorStore()
builder = Builder()  # Shared instance for doc synthesis


class Query(BaseModel):
    question: str
    n_results: int = 5
    fetch_fresh: bool = False  # NEW: fetch fresh data from APIs


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/stats")
def stats():
    return {
        "total_events": store.count(),  # ChromaDB count
        "chroma_db_count": store.count(),  # Make it clear this is ChromaDB
    }


@app.get("/latest")
def latest_events(limit: int = 10):
    """Get truly latest events from ChromaDB by sorting metadata"""
    try:
        # Fetch a larger pool to allow sorting by timestamp (ChromaDB get doesn't support order_by)
        results = store.collection.get(limit=100, include=["documents", "metadatas"])

        events = []
        for i in range(len(results["ids"])):
            events.append(
                {
                    "id": results["ids"][i],
                    "document": (
                        results["documents"][i][:150] if results["documents"] else ""
                    ),
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                }
            )

        # Sort by timestamp descending
        events.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)

        return {"events": events[:limit]}
    except Exception as e:
        return {"events": [], "error": str(e)}


@app.post("/query")
def query(q: Query):
    all_events = []

    # 1. Optionally fetch fresh data from APIs
    if q.fetch_fresh:
        # Extract keywords from question for targeted news fetch
        keywords = [
            w
            for w in q.question.lower().split()
            if w
            in [
                "earthquake",
                "flood",
                "wildfire",
                "cyclone",
                "hurricane",
                "tsunami",
                "volcano",
                "storm",
                "disaster",
            ]
        ]

        fresh_events = fetcher.fetch_fresh_data(keywords if keywords else None)

        # Embed question once for comparison
        question_embedding = embedder.embed(q.question)

        # Quick embed fresh data and calculate real similarity
        for event in fresh_events:
            # Create comprehensive document using unified logic
            doc = builder._synthesize_document(event)
            event_embedding = embedder.embed(doc)

            # Calculate cosine distance (1.0 - cosine_similarity)
            import numpy as np

            similarity = float(np.dot(question_embedding, event_embedding))
            distance = 1.0 - similarity

            # We skip low relevance fresh data too for consistency
            if distance <= 0.8:
                all_events.append(
                    {
                        "id": event["event_id"],
                        "document": doc,
                        "metadata": event,
                        "distance": distance,
                        "confidence": similarity,
                        "fresh": True,
                    }
                )

    # 2. Retrieve from vector store
    stored_events = retriever.retrieve(q.question, n=q.n_results)
    all_events.extend(stored_events)

    # 3. Enrich with GDELT news context
    news_context = enricher.enrich(q.question, all_events[: q.n_results])

    # 4. Generate answer with both events and news
    answer = generator.generate(q.question, all_events[: q.n_results], news_context)

    return {
        "answer": answer,
        "sources": all_events[: q.n_results],
        "news_articles": news_context["articles"],
        "fresh_data_count": len([e for e in all_events if e.get("fresh")]),
    }


def main():
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
