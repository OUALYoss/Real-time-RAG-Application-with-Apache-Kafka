from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ..rag.retriever import Retriever
from ..rag.generator import Generator
from ..embedding.vector_store import VectorStore
import uvicorn


app = FastAPI(title="Disaster RAG API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


retriever = Retriever()
generator = Generator()
store = VectorStore()


class Query(BaseModel):
    question: str
    n_results: int = 5
    duration_hours: int = None


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/stats")
def stats():
    return {"total_events": store.count()}


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
            # Create comprehensive document from event
            doc = event.get("description", "")
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
    events = retriever.retrieve(q.question, n=q.n_results, duration_hours=q.duration_hours)
    answer = generator.generate(q.question, events)
    return {"answer": answer, "sources": events}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
