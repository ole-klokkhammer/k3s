from typing import List, Dict
from pydantic import BaseModel
from openai import OpenAI
from ..config import WINDOW_SIZE, vLLM_URL
from .client import openai_client


class SessionState(BaseModel):
    """Represents the state of a chat session."""

    l1: List[Dict] = []
    l2: str = "Start of conversation."


class SessionService:
    def __init__(self, client: OpenAI = openai_client):
        self.sessions: Dict[str, SessionState] = {}
        self.client = client

    def get_state(self, session_id: str) -> SessionState:
        return self.sessions.get(session_id, SessionState())

    def update_state(self, session_id: str, l1: List[Dict], l2: str):
        self.sessions[session_id] = SessionState(l1=l1, l2=l2)

    def compact_l1_to_l2(self, session_id: str, history: List[Dict]) -> str:
        """Summarizes L1 overflow into L2 summary using Gemma 4."""
        state = self.get_state(session_id)
        current_l2 = state.l2
        overflow = history[:WINDOW_SIZE]  # Oldest turns

        prompt = f"Current Summary: {current_l2}\n\nNew turns to compact:\n{overflow}\n\nUpdate the summary concisely."
        resp = self.client.chat.completions.create(
            model="gemma4-31b-it", messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content


session_service = SessionService()
