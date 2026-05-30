import os 
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
print("MONGODB_URI = ", uri)

client = MongoClient(uri)


print(client.list_database_names())

db = client["El-Plan-STEM"]

print(db.list_collection_names())