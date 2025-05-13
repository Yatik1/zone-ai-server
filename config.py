import os 
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")
GEMINI_SECRET_KEY = os.getenv("GEMINI_SECRET_KEY")

QDRANT_URL = "http://localhost:6333"

MODEL_NAME="gemini-2.0-flash"