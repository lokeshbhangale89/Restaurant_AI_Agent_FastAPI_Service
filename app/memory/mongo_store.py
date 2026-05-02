from pymongo import MongoClient
from datetime import datetime
import uuid

client = MongoClient("mongodb://localhost:27017")

db = client["ai_engine"]
chat_collection = db["chat_history"]
session_collection = db["sessions"]


# =========================
# SESSION
# =========================
def get_or_create_session(user_id: str):
    session = session_collection.find_one({"user_id": user_id})

    if session:
        return session["session_id"]

    session_id = f"session-{uuid.uuid4()}"

    session_collection.insert_one({
        "user_id": user_id,
        "session_id": session_id,
        "created_at": datetime.utcnow()
    })

    return session_id


# =========================
# STORE CHAT (FAST)
# =========================
def store_chat(user_id, session_id, user_msg, ai_msg):
    try:
        chat_collection.update_one(
            {"user_id": user_id, "session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": user_msg},
                            {"role": "ai", "content": ai_msg}
                        ]
                    }
                }
            },
            upsert=True
        )
    except Exception as e:
        print("Mongo error:", e)


def store_chat_async(user_id, session_id, user_msg, ai_msg):
    store_chat(user_id, session_id, user_msg, ai_msg)


# =========================
# FETCH CHAT
# =========================
def get_conversation(user_id, session_id):
    doc = chat_collection.find_one({
        "user_id": user_id,
        "session_id": session_id
    })

    return doc.get("messages", []) if doc else []