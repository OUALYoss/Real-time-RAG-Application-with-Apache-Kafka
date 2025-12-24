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


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/stats")
def stats():
    return {"total_events": store.count()}


@app.post("/query")
def query(q: Query):
    events = retriever.retrieve(q.question, n=q.n_results)
    answer = generator.generate(q.question, events)
    return {"answer": answer, "sources": events}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
