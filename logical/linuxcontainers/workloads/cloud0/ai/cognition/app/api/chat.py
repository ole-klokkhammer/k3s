from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, AsyncGenerator
from openai import OpenAI

from ..config import vLLM_URL, WINDOW_SIZE
from ..core.memory import fetch_l3_context
from ..core.session import SessionService, session_service
from ..core.embedder import Embedder, embedder_service
from ..core.client import openai_client


# --- Models ---
class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    context_tier: Dict[str, Any]  # L1, L2, L3 details


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("")
async def chat(
    req: ChatRequest,
    session: SessionService = Depends(lambda: session_service),
    embedder: Embedder = Depends(lambda: embedder_service),
    client: OpenAI = Depends(lambda: openai_client),
):
    state = session.get_state(req.session_id)
    l1 = state.l1
    l2 = state.l2

    # 1. L3 Retrieval (Vector)
    l3_context = fetch_l3_context(req.message, embedder)

    # 2. Combine Context for Prompt
    full_context = (
        f"L3 (Knowledge): {l3_context}\nL2 (Summary): {l2}\nL1 (History): {l1}"
    )

    # 3. Get Response from Gemma 4 (Streaming)
    messages = [{"role": "system", "content": f"Context:\n{full_context}"}]
    messages.append({"role": "user", "content": req.message})

    def stream_response():
        full_text = ""
        stream = client.chat.completions.create(
            model="gemma4-31b-it", messages=messages, stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_text += content
            yield content

        # Update L1 and check for L2 Compaction after streaming completes
        l1.append({"role": "user", "content": req.message})
        l1.append({"role": "assistant", "content": full_text})

        if len(l1) > WINDOW_SIZE * 2:
            new_l2 = session.compact_l1_to_l2(req.session_id, l1)
            l1 = l1[WINDOW_SIZE * 2 :]

        session.update_state(req.session_id, l1, new_l2 if "new_l2" in locals() else l2)

    return StreamingResponse(stream_response())
