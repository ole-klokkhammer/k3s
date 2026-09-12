from sentence_transformers import SentenceTransformer
from ..config import EMBEDDING_MODEL

class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)

    def encode(self, text: str):
        return self.model.encode(text).tolist()

# Singleton instance for DI
embedder_service = Embedder()
