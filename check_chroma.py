import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_collection("disaster_events")
print(f"Total documents in collection: {collection.count()}")
results = collection.get(limit=5, include=["metadatas", "documents"])
for i, metadata in enumerate(results["metadatas"]):
    print(
        f"ID: {results['ids'][i]}, Source: {metadata.get('source')}, Type: {metadata.get('type')}"
    )
