# Disaster RAG System

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Start infrastructure
docker-compose up -d

# 3. Start producers (Terminal 1)
python -m src.ingestion.main

# 4. Start API (Terminal 2)
uvicorn src.api.main:app --reload

# 5. Start dashboard (Terminal 3)
streamlit run dashboard/app.py
```

## URLs
- Dashboard: http://localhost:8501
- API: http://localhost:8080/docs
- Kafka UI: http://localhost:8090
