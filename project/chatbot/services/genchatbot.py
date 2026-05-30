"""

import os
import random
import google.generativeai as genai
from pymongo import MongoClient
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from ml_models.model_momentum_new import predict_race_momentum
from ml_models.model_podium_new import predict_driver_podium
from ml_models.model_turn_new import predict_turn_severity

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["El-Plan-STEM"]
circuits_collection = db["circuits"]
lap_times_collection = db["lap_times"]
drivers_collection = db["drivers"]
pit_stops_collection = db["pit_stops"]
races_collection = db["races"]

# SentenceTransformers for embeddings
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Gemini API setup
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
generation_config = {
    "temperature": 1.2,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings=safety_settings,
    generation_config=generation_config,
    system_instruction='''
You are an expert Formula 1 assistant. Provide accurate and useful F1-related information and predictions based on data and user questions.
'''
)
chat_session = model.start_chat(history=[])

# Example driver/circuit lists (expand or pull from DB as needed)
known_drivers = drivers_collection.aggregate([{ "$sample": { "size": 1 } }]).next()
driver = drivers_collection.find_one({"driverRef": known_drivers["driverRef"]})
known_circuits = circuits_collection.aggregate([{ "$sample": { "size": 1 } }]).next()
circuit = circuits_collection.find_one({"circuitRef": known_circuits["circuitRef"]})


def extract_driver_name(user_input):
    for name in known_drivers:
        if name.lower() in user_input.lower():
            return name
    return None

def extract_circuit_name(user_input):
    for name in known_circuits:
        if name.lower() in user_input.lower():
            return name
    return None

def get_chat_response(user_input):
    user_input_lower = user_input.lower()

    # Route to podium prediction
    if "podium" in user_input_lower or "top 3" in user_input_lower:
        driver = extract_driver_name(user_input)
        if driver:
            return predict_driver_podium(driver)
        return "Which driver are you asking about?"

    # Route to momentum prediction
    elif "momentum" in user_input_lower or "form" in user_input_lower:
        driver = extract_driver_name(user_input)
        if driver:
            return predict_race_momentum(driver)
        return "Which driver's momentum are you asking about?"

    # Route to turn severity
    elif "turn severity" in user_input_lower or "corners" in user_input_lower:
        circuit = extract_circuit_name(user_input)
        if circuit:
            return predict_turn_severity(circuit)
        return "Which circuit are you referring to?"

    # Fallback to Gemini
    else:
        response = chat_session.send_message(user_input)
        return response.text

if __name__ == "__main__":
    print("F1 Chatbot is ready. Ask me anything about drivers, circuits, or predictions!\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Bot: Goodbye!")
            break
        response = get_chat_response(user_input)
        print(f"Bot: {response}\n")

"""