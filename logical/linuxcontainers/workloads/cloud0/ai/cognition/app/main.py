import os
from fastapi import FastAPI
from .api.chat import router as chat_router

app = FastAPI(title="Cognition Proxy")
app.include_router(chat_router)
