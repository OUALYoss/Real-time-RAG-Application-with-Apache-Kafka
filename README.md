# Disaster RAG System

A real-time Retrieval-Augmented Generation (RAG) pipeline for disaster monitoring using Apache Kafka, ChromaDB, and a compact LLM for on-demand generation.

---

## Quick Start ✅

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Start infrastructure (Kafka, ChromaDB, etc.)

```bash
docker-compose up -d
```

3. Start the complete pipeline (convenience)

```bash
python main.py all
```

4. Or start components separately

```bash
python -m src.ingestion.main    # Terminal 1: Data ingestion
python -m src.processing.main   # Terminal 2: Data processing
python -m src.rag.builder       # Terminal 3: Embedding & storage
python -m src.api.main          # Terminal 4: API server
streamlit run dashboard/app.py  # Dashboard
```

---

## Embedding & Retrieval Pipeline 🔧

**High-level:** events are synthesized into short natural-language documents, encoded with a SentenceTransformer, stored in ChromaDB, and retrieved via single-vector cosine search.

### Components

- **Embedding** (`src/embedding/embedder.py`)
  - Model: `SentenceTransformer('all-MiniLM-L6-v2')`
  - Embeddings are normalized at encode time for cosine similarity.

- **Storage / Vector DB** (`src/embedding/vector_store.py`)
  - ChromaDB HTTP client, collection: `disaster_events` (cosine space).

- **Indexing / Ingestion** (`src/rag/builder.py`)
  - `_synthesize_document(event)` converts structured event JSON into a compact natural-language document (event type, place, time, and short description) to improve embedding relevance.
  - Batch embedding/upsert performed for efficiency.

- **Retrieval** (`src/rag/retriever.py`)
  - Query is embedded (single-vector) and Chroma is queried for nearest neighbors.
  - Results filtered using a distance threshold (default ≈ 0.8), and a confidence score is computed as `confidence = max(0, 1 - distance)`.

- **Fetch-Live / On-Demand** (`src/api/main.py`)
  - When `fetch_fresh` is requested, APIs are polled, documents are synthesized and embedded on-the-fly, and similarity is computed directly via dot product (similarity) with the question embedding.
  - Fresh results are merged with stored results before enrichment and generation.

- **Latest Arrivals**
  - `GET /latest` fetches a candidate pool from ChromaDB and **chronologically re-ranks** by metadata timestamp so users see the most recent anomalies.

---

## ColBERT: Is it relevant? 🤔

- **Short answer:** No — ColBERT (late-interaction / token-level matching) is **not** used in this project. The codebase uses single-vector dense embeddings + ChromaDB.
- You may see incidental references to "ColBERT-like" scoring inside installed transformer packages, but there is no ColBERT integration in `src/`.

### When to consider ColBERT
- Use ColBERT if you need finer-grained token/phrase matching or multi-vector representations per document (better phrase recall/precision), especially for complex queries where single-vector representations fail.
- Tradeoffs: better precision on phrase matches vs **higher complexity** — token encodings, multi-vector indices, different indexing tech (Faiss or specialized ColBERT implementations), larger storage, and higher query cost.

---

## Files of interest 📁

- `src/embedding/embedder.py`  — embedding model and helpers
- `src/embedding/vector_store.py` — ChromaDB client & search
- `src/rag/builder.py` — document synthesis & batch upsert
- `src/rag/retriever.py` — retrieval and filtering
- `src/api/main.py` — API endpoints (`/query`, `/latest`, fetch-live) and merge logic
- `dashboard/app.py` — Streamlit dashboard UI

---

## Next steps (options) ��

- I can map where to add a ColBERT-style retriever (files and infra changes). 
- I can prototype a ColBERT retrieval path (e.g., Faiss + multi-vector handling) and provide a small benchmark vs the current approach.
- I can produce a short implementation plan with estimated effort and tradeoffs.

If you want any of the above, tell me which option to proceed with.

---

### URLs

- Dashboard: http://localhost:8501
- API docs: http://localhost:8080/docs
- Kafka UI: http://localhost:8090

*Last updated:* 2025-12-27
