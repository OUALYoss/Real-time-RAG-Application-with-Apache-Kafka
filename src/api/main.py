from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.retriever import Retriever
from rag.generator import Generator
from embedding.vector_store import VectorStore
import uvicorn
from rag.news_enricher import NewsEnricher

app = FastAPI(title="Disaster RAG API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


retriever = Retriever()
generator = Generator()
store = VectorStore()


class Query(BaseModel):
    question: str
    n_results: int = 10
    duration_hours: int = 24


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/stats")
def stats():
    return {"total_events": store.count()}


@app.get("/test_embed")
def test_embed():
    try:
        emb = retriever.embedder.embed("test")
        return {"length": len(emb)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/latest")
def latest_events(limit: int = 10):
    """Get truly latest events from ChromaDB by fetching the last added records."""
    try:
        total_count = store.count()
        pool_size = 100
        # Fetch the last 'pool_size' entries by setting an offset
        offset = max(0, total_count - pool_size)

        results = store.collection.get(
            limit=pool_size, offset=offset, include=["documents", "metadatas"]
        )

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

        # Sort by timestamp_ts if available, otherwise fallback to timestamp string
        events.sort(
            key=lambda x: x["metadata"].get("timestamp_ts")
            or x["metadata"].get("timestamp", ""),
            reverse=True,
        )

        return {"events": events[:limit]}
    except Exception as e:
        return {"events": [], "error": str(e)}


@app.post("/query")
def query(q: Query):
    all_events = []

    # 1. Retrieve from vector store
    stored_events = retriever.retrieve(
        q.question, n=q.n_results, duration_hours=q.duration_hours
    )
    print(f"Debug: stored_events = {len(stored_events)}")
    all_events.extend(stored_events)

    # 2. Enrich with GDELT news context
    enricher = NewsEnricher()
    news_context = enricher.enrich(q.question, all_events[: q.n_results])

    # 3. Generate answer with both events and news
    answer = generator.generate(q.question, all_events[: q.n_results], news_context)

    return {
        "answer": answer,
        "sources": all_events[: q.n_results],
        "news_articles": news_context["articles"],
        "debug": f"stored_events: {len(all_events)}",
    }


def main():
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
