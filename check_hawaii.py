import chromadb
import time
from datetime import datetime, timezone

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_or_create_collection("disaster_events")

# Get events mentioning Hawaii
results = collection.get(
    where_document={"$contains": "Hawaii"}, include=["documents", "metadatas"]
)

now_ts = int(time.time())
print(f"Current UTC timestamp: {now_ts}")

for i in range(len(results["ids"])):
    meta = results["metadatas"][i]
    ts = meta.get("timestamp_ts")
    print(f"ID: {results['ids'][i]}")
    print(f"Doc: {results['documents'][i][:200]}...")
    print(f"TS: {ts} (Diff: {now_ts - ts if ts else 'N/A'}s)")
    print("-" * 20)
