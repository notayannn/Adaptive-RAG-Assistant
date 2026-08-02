import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    print("⚠️ WARNING: Qdrant URL or API Key is missing in .env")

if not GROQ_API_KEY:
    print("⚠️ WARNING: Groq API Key is missing in .env")

COLLECTION_NAME = "rag_knowledge_base"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


CHUNK_SIZE = 500 
CHUNK_OVERLAP = 50

LLM_MODEL_NAME = "llama-3.3-70b-versatile"


DEFAULT_TOP_K = 3
DEFAULT_SIMILARITY_THRESHOLD = 0.10
DEFAULT_TEMPERATURE = 0.1

# --- UI Slider Ranges ---
TEMP_MIN = 0.0
TEMP_MAX = 1.0
TEMP_STEP = 0.05

TOP_K_MIN = 1
TOP_K_MAX = 10
TOP_K_STEP = 1

THRESHOLD_MIN = 0.0
THRESHOLD_MAX = 1.0
THRESHOLD_STEP = 0.05