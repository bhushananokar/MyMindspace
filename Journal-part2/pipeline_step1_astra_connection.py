import os
import json
from uuid import UUID
from dotenv import load_dotenv
from astrapy import DataAPIClient

# Load env vars
load_dotenv()

API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
API_TOKEN = os.getenv("ASTRA_DB_TOKEN")
KEYSPACE = os.getenv("KEYSPACE", "default_keyspace")
COLLECTION = os.getenv("COLLECTION", "chat_embeddings")   # or "memory_embeddings" if that's created

# Connect client
client = DataAPIClient(API_TOKEN)
db = client.get_database_by_api_endpoint(API_ENDPOINT)
collection = db.get_collection(COLLECTION, keyspace=KEYSPACE)

# Query memory embeddings for user_id "123"
# Modify the query syntax if needed, depending on how your records are stored
query = {"user_id": "123"}  # Filter records

docs = collection.find(query)

formatted_results = []

for doc in docs:
    # Remap/transform as needed for the target schema
    result = {
        "id": str(doc.get('id', '')),  # Make sure this is UUID format in your DB
        "user_id": doc.get('user_id', ''),
        "memory_type": doc.get('memory_type', ''),
        "content_summary": doc.get('content_summary', ''),
        "importance_score": doc.get('importance_score', 0.0),
        "gate_scores": json.dumps(doc.get('gate_scores', {})),  # ensure JSON string
        "feature_vector": doc.get('feature_vector', []),
        "created_at": doc.get('created_at', ''),
        "last_accessed": doc.get('last_accessed', ''),
        "access_frequency": doc.get('access_frequency', 0),
        "emotional_significance": doc.get('emotional_significance', 0.0),
        "temporal_relevance": doc.get('temporal_relevance', 0.0),
        "relationships": doc.get('relationships', []),
        "context_needed": json.dumps(doc.get('context_needed', {})),
        "retrieval_triggers": doc.get('retrieval_triggers', []),
        "original_entry_id": str(doc.get('original_entry_id', '')),
    }
    formatted_results.append(result)

# Example: Print or store as needed
for item in formatted_results:
    print(json.dumps(item, indent=2))

# To save as JSON file:
with open("memory_embeddings_user_123.json", "w") as f:
    json.dump(formatted_results, f, indent=2)

print("Fetched and stored embeddings for user_id 123!")
