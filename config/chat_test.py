import os 
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print("GOOGLE_API_KEY = ", api_key)