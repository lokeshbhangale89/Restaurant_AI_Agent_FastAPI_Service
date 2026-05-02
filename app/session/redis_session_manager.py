import redis
import json
import threading
from datetime import timedelta
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

SESSION_TTL = 1800  # 30 mins

summary_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0
)


class RedisSessionManager:

    def _key(self, user_id, session_id):
        return f"session:{user_id}:{session_id}"

    # =========================
    # 📥 GET CONTEXT
    # =========================
    def get_full_context(self, user_id, session_id):
        data = redis_client.get(self._key(user_id, session_id))

        if not data:
            return {"summary": "", "messages": []}

        try:
            return json.loads(data)
        except:
            return {"summary": "", "messages": []}

    # =========================
    # 🧠 SET HISTORY
    # =========================
    def set_history(self, user_id, session_id, messages):
        try:
            data = {
                "summary": "",
                "messages": messages
            }

            redis_client.setex(
                self._key(user_id, session_id),
                timedelta(seconds=SESSION_TTL),
                json.dumps(data)
            )

        except Exception as e:
            print("❌ Redis set_history error:", str(e))

    # =========================
    # 🧠 CORE SUMMARY FUNCTION (USED BY BOTH SYNC + ASYNC)
    # =========================
    def _generate_summary(self, old_messages, existing_summary):

        def safe_to_str(x):
            if isinstance(x, (list, dict)):
                return json.dumps(x)
            return str(x)

        text = "\n".join([safe_to_str(m["content"]) for m in old_messages])

        prompt = f"""
Summarize conversation focusing on:
- User intent
- Items added/removed in cart
- Preferences (veg/non-veg, spicy, etc.)

Keep it concise.

Previous summary:
{existing_summary}

New messages:
{text}
"""

        response = summary_llm.invoke(prompt)
        return str(response.content)

    # =========================
    # ➕ APPEND MESSAGE
    # =========================
    def append(self, user_id, session_id, message):
        key = self._key(user_id, session_id)

        data = self.get_full_context(user_id, session_id)

        messages = data.get("messages", [])
        summary = data.get("summary", "")

        messages.append({
            "type": "human" if isinstance(message, HumanMessage) else "ai",
            "content": message.content
        })

        # 🔥 ASYNC SUMMARY
        if len(messages) > 6:
            old_messages = messages[:-6]
            messages = messages[-6:]

            threading.Thread(
                target=self._async_summarize_and_update,
                args=(user_id, session_id, old_messages, summary),
                daemon=True
            ).start()

        redis_client.setex(
            key,
            timedelta(seconds=SESSION_TTL),
            json.dumps({
                "summary": summary,
                "messages": messages
            })
        )

        return summary

    # =========================
    # ⚡ ASYNC SUMMARY
    # =========================
    def _async_summarize_and_update(self, user_id, session_id, old_messages, existing_summary):
        try:
            new_summary = self._generate_summary(old_messages, existing_summary)

            key = self._key(user_id, session_id)
            data = self.get_full_context(user_id, session_id)

            redis_client.setex(
                key,
                timedelta(seconds=SESSION_TTL),
                json.dumps({
                    "summary": new_summary,
                    "messages": data.get("messages", [])
                })
            )

        except Exception as e:
            print("❌ Async Summary error:", e)

    # =========================
    # 🧹 CLEAR SESSION
    # =========================
    def clear(self, user_id, session_id):
        redis_client.delete(self._key(user_id, session_id))


# Singleton
session_manager = RedisSessionManager()