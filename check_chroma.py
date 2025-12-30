import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_collection("disaster_events")
results = collection.get(limit=5, include=["metadatas"])
for i, metadata in enumerate(results["metadatas"]):
    print(
        f"ID: {results['ids'][i]}, Timestamp TS: {metadata.get('timestamp_ts')}, Timestamp: {metadata.get('timestamp')}"
    )
