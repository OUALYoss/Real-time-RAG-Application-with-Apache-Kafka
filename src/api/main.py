from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
from kafka import KafkaConsumer
from ..rag.retriever import Retriever
from ..rag.generator import Generator

app = FastAPI(title="Disaster RAG API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

events_cache = {}
retriever = None
generator = None


class QueryRequest(BaseModel):
    question: str
    n_results: int = 9


def load_events_from_kafka(max_events: int = 5000):
    try:
        consumer = KafkaConsumer(
            "processed-events",
            bootstrap_servers="localhost:9092",
            auto_offset_reset="earliest",
            consumer_timeout_ms=15000,
            value_deserializer=lambda m: json.loads(m.decode()),
        )
        count = 0
        for message in consumer:
            event = message.value
            events_cache[event["event_id"]] = event
            count += 1
            if count >= max_events:
                break
        consumer.close()
    except Exception:
        pass


@app.on_event("startup")
def startup():
    global retriever, generator
    load_events_from_kafka()
    retriever = Retriever()
    generator = Generator()


@app.get("/")
def root():
    return {"status": "running", "events_loaded": len(events_cache)}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    sources = {}
    types = {}
    for e in events_cache.values():
        src = e.get("source", "unknown")
        typ = e.get("event_type", "unknown")
        sources[src] = sources.get(src, 0) + 1
        types[typ] = types.get(typ, 0) + 1
    return {
        "total_events": len(events_cache),
        "by_source": sources,
        "by_type": types,
    }


@app.get("/events")
def list_events(
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=150, le=5000),
):
    results = list(events_cache.values())

    if event_type:
        results = [e for e in results if e.get("event_type") == event_type]
    if source:
        results = [e for e in results if e.get("source") == source]
    if severity:
        results = [e for e in results if e.get("severity") == severity]

    results = sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)
    return results[:limit]


@app.get("/events/{event_id}")
def get_event(event_id: str):
    if event_id in events_cache:
        return events_cache[event_id]
    return {"error": "Event not found"}


@app.get("/events/refresh")
def refresh_events():
    load_events_from_kafka()
    return {"status": "refreshed", "total_events": len(events_cache)}


@app.post("/query")
def query(req: QueryRequest):
    events = retriever.retrieve(req.question, n=req.n_results)
    answer = generator.generate(req.question, events)
    return {
        "answer": answer,
        "question": req.question,
        "sources": events,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
