from typing import Dict, Any

# --- Configuration ---
DB_CONFIG = {
    "dbname": "cognition",
    "user": "postgres",
    "password": "password", # Update based on your environment
    "host": "localhost"
}
vLLM_URL = "http://localhost:8000/v1" # Gemma 4 endpoint
WINDOW_SIZE = 5  # L1 Buffer size before compaction
EMBEDDING_MODEL = "all-MiniLM-L6-v2" # 384-dim for skills
