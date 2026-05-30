import os
import google.generativeai as genai  # type: ignore
from pymongo import MongoClient # type: ignore
from dotenv import load_dotenv  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore
import numpy as np  # type: ignore

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["formula1_db"]
circuits_collection = db["circuits"]
lap_times_collection = db["lap_times"]

# SentenceTransformers for embeddings
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Gemini API setup
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
generation_config = {
    "temperature": 1,
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
    model_name="gemini-2.5-flash",
    safety_settings=safety_settings,
    generation_config=generation_config,
    system_instruction='''You are an expert educator and Formula 1 enthusiast. Use provided Formula 1 data to generate science-related questions (e.g., physics or math) themed around Formula 1. Wait for the student's answer. If correct, congratulate them and offer another question. If incorrect, explain the answer using fun, easy-to-understand F1 analogies.'''
)
chat_session = model.start_chat(history=[])

def generate_embedding(text):
    """Generate embedding for a text string using SentenceTransformers."""
    return embedder.encode(text, convert_to_numpy=True).tolist()

def vector_search(query, collection, field="description_embedding", limit=1):
    """Perform vector search in MongoDB."""
    query_embedding = generate_embedding(query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": field,
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": limit
            }
        },
        {
            "$project": {
                "name": 1,
                "length": 1,  # Assume circuit length in km
                "location": 1,
                "circuitId": 1,
                "_id": 0,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    return list(collection.aggregate(pipeline))

def get_chat_response(user_input, retrieved_data=None, correct_answer=None):
    """Get chatbot response, using retrieved data for RAG and verifying answers."""
    try:
        if retrieved_data and not user_input:  # Generate new question
            prompt = f"""
            Using the Formula 1 data: {retrieved_data}
            Generate a physics or math question themed around Formula 1. Include the correct answer for verification. Format the response as:
            Question: [Your question here]
            (Correct answer: [Answer])
            """
            response = chat_session.send_message(prompt)
            model_response = response.text
            chat_session.history.append({
                "role": "model",
                "parts": [model_response],
                "correct_answer": correct_answer,
                "retrieved_data": retrieved_data
            })
        else:  # Handle user answer
            last_message = chat_session.history[-1] if chat_session.history else None
            if last_message and "correct_answer" in last_message:
                correct_answer = last_message["correct_answer"]
                try:
                    user_answer = float(user_input.strip())  # Assume numerical answer
                    if abs(user_answer - correct_answer) < 0.1:  # Tolerance
                        prompt = "Correct! Great job! Would you like another question?"
                    else:
                        prompt = f"""
                        Incorrect. The correct answer is {correct_answer}. Explain why using a fun Formula 1 analogy, based on the data: {last_message['retrieved_data']}.
                        """
                except ValueError:
                    prompt = "Please provide a numerical answer."
            else:
                prompt = user_input
            response = chat_session.send_message(prompt)
            model_response = response.text
            chat_session.history.append({"role": "user", "parts": [user_input]})
            chat_session.history.append({"role": "model", "parts": [model_response]})
        return model_response
    except Exception as e:
        return f"Error: {str(e)}"

# Terminal interface
if __name__ == "__main__":
    print("Bot: Ready to ask a Formula 1 science question!")
    print()

    # Example: Vector search to retrieve relevant circuit
    query = "Monaco Grand Prix circuit"
    circuit_docs = vector_search(query, circuits_collection)
    
    if circuit_docs:
        circuit = circuit_docs[0]
        lap_time_doc = lap_times_collection.find_one({"circuitId": circuit["circuitId"]})
        if lap_time_doc:
            lap_time_sec = lap_time_doc["milliseconds"] / 1000
            circuit_length_km = circuit["length"]
            speed_kmh = (circuit_length_km / (lap_time_sec / 3600))  # km/h
            retrieved_data = {
                "circuit": circuit["name"],
                "location": circuit["location"],
                "lap_time_sec": lap_time_sec,
                "circuit_length_km": circuit_length_km,
                "speed_kmh": round(speed_kmh, 2)
            }
            correct_answer = retrieved_data["speed_kmh"]
            response = get_chat_response("", retrieved_data, correct_answer)
        else:
            response = "No lap time data found for this circuit."
    else:
        response = "No relevant circuit found."
    
    print(f"Bot: {response}")
    print()

    while True:
        user_input = input("You: ")
        print()
        response = get_chat_response(user_input)
        print(f"Bot: {response}")
        print()