import os

PROJECT = ""

FILES = {
    # =============================================================================
    # DOCKER-COMPOSE
    # =============================================================================
    "docker-compose.yml": """version: "3.8"
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports:
      - "8090:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
""",
    # =============================================================================
    # REQUIREMENTS
    # =============================================================================
    "requirements.txt": """kafka-python==2.0.2
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
apscheduler==3.10.4
pydantic==2.5.3
python-dotenv==1.0.0
feedparser==6.0.11
sentence-transformers==2.3.1
chromadb==0.4.22
ollama==0.1.6
streamlit==1.31.0
plotly==5.18.0
requests==2.31.0
""",
    # =============================================================================
    # ENV
    # =============================================================================
    ".env.example": """KAFKA_BOOTSTRAP_SERVERS=localhost:9092
OPENWEATHER_API_KEY=your_key
NEWS_API_KEY=your_key
NASA_FIRMS_MAP_KEY=your_key
OLLAMA_MODEL=llama3.2
""",
    # =============================================================================
    # SRC/INGESTION
    # =============================================================================
    "src/__init__.py": "",
    "src/ingestion/__init__.py": "",
    "src/ingestion/config.py": """import os
from dotenv import load_dotenv
load_dotenv()

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPICS = {
    "earthquakes": "raw-earthquakes",
    "disasters": "raw-disasters",
    "weather": "raw-weather",
    "wildfires": "raw-wildfires",
    "news": "raw-news",
}
""",
    "src/ingestion/producer.py": """import json
from kafka import KafkaProducer
from datetime import datetime
from .config import KAFKA_SERVERS

class BaseProducer:
    def __init__(self, topic: str):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode()
        )
    
    def send(self, key: str, data: dict):
        data["ingested_at"] = datetime.utcnow().isoformat() + "Z"
        self.producer.send(self.topic, key=key.encode(), value=data)
        self.producer.flush()
        print(f"[{self.topic}] Sent: {key}")
""",
    "src/ingestion/usgs_producer.py": """import requests
from datetime import datetime
from .producer import BaseProducer
from .config import TOPICS

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

class USGSProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["earthquakes"])
    
    def fetch_and_send(self):
        resp = requests.get(USGS_URL, timeout=30)
        data = resp.json()
        
        for feature in data.get("features", []):
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            
            event = {
                "event_id": f"usgs_{feature['id']}",
                "event_type": "earthquake",
                "source": "USGS",
                "timestamp": datetime.utcfromtimestamp(props["time"]/1000).isoformat() + "Z",
                "latitude": coords[1],
                "longitude": coords[0],
                "magnitude": props.get("mag"),
                "place": props.get("place"),
                "title": props.get("title"),
            }
            self.send(event["event_id"], event)

if __name__ == "__main__":
    USGSProducer().fetch_and_send()
""",
    "src/ingestion/gdacs_producer.py": """import feedparser
from .producer import BaseProducer
from .config import TOPICS

GDACS_URL = "https://gdacs.org/xml/rss.xml"

class GDACSProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["disasters"])
    
    def fetch_and_send(self):
        feed = feedparser.parse(GDACS_URL)
        
        for entry in feed.entries:
            event = {
                "event_id": f"gdacs_{entry.get('gdacs_eventid', '')}",
                "event_type": entry.get("gdacs_eventtype", "disaster"),
                "source": "GDACS",
                "timestamp": entry.get("published", ""),
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "alert_level": entry.get("gdacs_alertlevel", ""),
                "latitude": float(entry.get("geo_lat", 0) or 0),
                "longitude": float(entry.get("geo_long", 0) or 0),
            }
            self.send(event["event_id"], event)

if __name__ == "__main__":
    GDACSProducer().fetch_and_send()
""",
    "src/ingestion/nws_producer.py": """import requests
from .producer import BaseProducer
from .config import TOPICS

NWS_URL = "https://api.weather.gov/alerts/active"

class NWSProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["weather"])
    
    def fetch_and_send(self):
        headers = {"User-Agent": "DisasterRAG/1.0"}
        resp = requests.get(NWS_URL, headers=headers, timeout=30)
        data = resp.json()
        
        for feature in data.get("features", [])[:20]:
            props = feature["properties"]
            event = {
                "event_id": f"nws_{props.get('id', '')}",
                "event_type": "weather_alert",
                "source": "NWS",
                "timestamp": props.get("sent", ""),
                "title": props.get("headline", ""),
                "description": props.get("description", "")[:500],
                "severity": props.get("severity", ""),
                "areas": props.get("areaDesc", ""),
            }
            self.send(event["event_id"], event)

if __name__ == "__main__":
    NWSProducer().fetch_and_send()
""",
    "src/ingestion/main.py": """from apscheduler.schedulers.blocking import BlockingScheduler
from .usgs_producer import USGSProducer
from .gdacs_producer import GDACSProducer
from .nws_producer import NWSProducer

def main():
    usgs = USGSProducer()
    gdacs = GDACSProducer()
    nws = NWSProducer()
    
    scheduler = BlockingScheduler()
    scheduler.add_job(usgs.fetch_and_send, "interval", seconds=60)
    scheduler.add_job(gdacs.fetch_and_send, "interval", seconds=300)
    scheduler.add_job(nws.fetch_and_send, "interval", seconds=120)
    
    print("Starting producers...")
    for p in [usgs, gdacs, nws]:
        try:
            p.fetch_and_send()
        except Exception as e:
            print(f"Error: {e}")
    
    scheduler.start()

if __name__ == "__main__":
    main()
""",
    # =============================================================================
    # SRC/EMBEDDING
    # =============================================================================
    "src/embedding/__init__.py": "",
    "src/embedding/embedder.py": """from sentence_transformers import SentenceTransformer

MODEL = "all-MiniLM-L6-v2"

class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(MODEL)
    
    def embed(self, text: str) -> list:
        return self.model.encode(text).tolist()
    
    def embed_event(self, event: dict) -> list:
        text = f"{event.get('title', '')} {event.get('description', '')} {event.get('place', '')}"
        return self.embed(text)
""",
    "src/embedding/vector_store.py": """import chromadb
from datetime import datetime

class VectorStore:
    def __init__(self, host="localhost", port=8000):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection("disaster_events")
    
    def add(self, event_id: str, embedding: list, document: str, metadata: dict):
        self.collection.add(
            ids=[event_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )
    
    def search(self, query_embedding: list, n=5) -> dict:
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"]
        )
    
    def count(self) -> int:
        return self.collection.count()
""",
    # =============================================================================
    # SRC/RAG
    # =============================================================================
    "src/rag/__init__.py": "",
    "src/rag/retriever.py": """from ..embedding.embedder import Embedder
from ..embedding.vector_store import VectorStore

class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()
    
    def retrieve(self, query: str, n=5) -> list:
        embedding = self.embedder.embed(query)
        results = self.store.search(embedding, n=n)
        
        events = []
        if results["ids"][0]:
            for i in range(len(results["ids"][0])):
                events.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                })
        return events
""",
    "src/rag/generator.py": """import ollama

PROMPT = '''Based on these disaster events, answer the question.

EVENTS:
{context}

QUESTION: {question}

Answer factually based on the data above:'''

class Generator:
    def __init__(self, model="llama3.2"):
        self.model = model
    
    def generate(self, question: str, events: list) -> str:
        context = "\\n".join([
            f"- [{e['metadata'].get('source')}] {e['document']}"
            for e in events
        ])
        
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": PROMPT.format(context=context, question=question)}]
        )
        return response["message"]["content"]
""",
    # =============================================================================
    # SRC/API
    # =============================================================================
    "src/api/__init__.py": "",
    "src/api/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ..rag.retriever import Retriever
from ..rag.generator import Generator
from ..embedding.vector_store import VectorStore

app = FastAPI(title="Disaster RAG API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
""",
    # =============================================================================
    # DASHBOARD
    # =============================================================================
    "dashboard/app.py": """import streamlit as st
import requests

API = "http://localhost:8080"

st.title("Disaster Monitor")

question = st.text_input("Question:", placeholder="Recent earthquakes in California?")

if st.button("Search"):
    if question:
        with st.spinner("Searching..."):
            try:
                r = requests.post(f"{API}/query", json={"question": question})
                data = r.json()
                st.success("Answer:")
                st.write(data["answer"])
                st.caption(f"Sources: {len(data['sources'])} events")
            except:
                st.error("API not available. Run: uvicorn src.api.main:app")

try:
    stats = requests.get(f"{API}/stats").json()
    st.sidebar.metric("Events", stats["total_events"])
except:
    st.sidebar.warning("API offline")
""",
    # =============================================================================
    # MAKEFILE
    # =============================================================================
    "Makefile": """up:
\tdocker-compose up -d

down:
\tdocker-compose down

producers:
\tpython -m src.ingestion.main

api:
\tuvicorn src.api.main:app --reload --port 8080

dashboard:
\tstreamlit run dashboard/app.py

install:
\tpip install -r requirements.txt
""",
    # =============================================================================
    # README
    # =============================================================================
    "README.md": """# Disaster RAG System

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
""",
}


def main():

    for path, content in FILES.items():
        full_path = os.path.join(PROJECT, path)
        os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content.strip() + "\n")
        print(f"✅ {path}")

    print(f"\n🎉 Projet créé: {PROJECT}/")
    print(f"   cd {PROJECT} && make install && make up")


if __name__ == "__main__":
    main()
