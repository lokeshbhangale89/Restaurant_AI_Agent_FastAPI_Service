from fastapi import FastAPI
from pydantic import BaseModel

from app.agent import run_agent
from app.memory.mongo_store import get_or_create_session

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    token: str
    user_id: str


@app.post("/chat")
def chat(req: ChatRequest):

    # ✅ ALWAYS same session per user
    session_id = get_or_create_session(req.user_id)

    response = run_agent(
        req.user_id,
        session_id,
        req.message,
        req.token
    )

    return {
        "userId": req.user_id,
        "sessionId": session_id,
        "message": response
    }