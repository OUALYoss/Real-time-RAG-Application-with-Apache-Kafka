# Disaster RAG System

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start infrastructure (Kafka, ChromaDB, etc.)
docker-compose up -d

# 3. Start Ollama and pull model if it's not done before
ollama serve
ollama pull llama3.2

# 4. Start the complete pipeline
python main.py all

# Alternative: Start components separately
python -m src.ingestion.main    # Terminal 1: Data ingestion
python -m src.processing.main   # Terminal 2: Data processing
python -m src.rag.builder   # Terminal 3: Embedding & storage
python -m src.api.main       # Terminal 4: API server

## URLs

- Dashboard: http://localhost:8501
- API: http://localhost:8081/docs
- Kafka UI: http://localhost:8090

# 6. Start dashboard (Terminal 3)

streamlit run dashboard/app.py

```

## URLs

- Dashboard: http://localhost:8501
- API: http://localhost:8080/docs
- Kafka UI: http://localhost:8090

```

```
