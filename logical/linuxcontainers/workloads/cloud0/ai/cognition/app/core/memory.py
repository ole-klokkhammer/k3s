import psycopg2
from ..config import DB_CONFIG
from .embedder import Embedder


class MemoryService:
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def fetch_l3_context(self, query: str, embedder: Embedder) -> str:
        """Retrieves semantic context from pgvector (L3)."""
        query_vec = embedder.encode(query)
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                # Search in skills table using cosine distance <->
                cur.execute(
                    "SELECT skill_name, description FROM skills ORDER BY embedding <-> %s LIMIT 3",
                    (query_vec,),
                )
                results = cur.fetchall()
                return "\n".join([f"Skill: {r[0]} -> {r[1]}" for r in results])


memory_service = MemoryService(DB_CONFIG)
