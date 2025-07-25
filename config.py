import os 
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")
GEMINI_SECRET_KEY = os.getenv("GEMINI_SECRET_KEY")

MODEL_NAME=os.getenv("MODEL_NAME")

BUCKET_NAME = os.getenv("BUCKET_NAME")
REGION_NAME = os.getenv("REGION_NAME")
ACCESS_KEY = os.getenv("ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

BACKEND_DB = os.getenv("BACKEND_PROD")

QDRANT_URL=os.getenv("QDRANT_URL")
QDRANT_KEY=os.getenv("QDRANT_API_KEY")