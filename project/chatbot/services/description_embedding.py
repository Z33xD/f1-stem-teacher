from pymongo import MongoClient  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore
from dotenv import load_dotenv # type: ignore
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["formula1_db"]
circuits_collection = db["circuits"]

embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings for circuit descriptions
for circuit in circuits_collection.find():
    description = f"{circuit['name']} in {circuit['location']}"
    embedding = embedder.encode(description, convert_to_numpy=True).tolist()
    circuits_collection.update_one(
        {"_id": circuit["_id"]},
        {"$set": {"description_embedding": embedding}}
    )

client.close()