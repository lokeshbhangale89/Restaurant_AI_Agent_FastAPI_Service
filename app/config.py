import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "user_memory"