from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

import time
import json
import traceback
from dotenv import load_dotenv

from app.prompt import SYSTEM_PROMPT
from app.tools.food_tools import (
    get_food_items,
    add_to_cart_api,
    clear_cart_api,
    remove_from_cart_api,
    get_cart_api
)

from app.memory.memory_store import fetch_relevant_chunks
from app.memory.mongo_store import store_chat_async, get_conversation
from app.session.redis_session_manager import session_manager

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0
)


# =========================
# 🔧 TOOLS
# =========================
def create_tools(token: str):

    @tool
    def food_items_tool(query: str) -> str:
        """Use ONLY for menu, food items, dishes, or recommendations."""
        return str(get_food_items(query))

    @tool
    def add_to_cart(product_name: str, quantity: int = 1) -> str:
        """Add item to cart."""
        return add_to_cart_api(token, product_name, quantity)

    @tool
    def get_cart() -> str:
        """View cart items."""
        return get_cart_api(token)

    @tool
    def remove_from_cart(product_name: str) -> str:
        """Remove item from cart."""
        return remove_from_cart_api(token, product_name)

    @tool
    def clear_cart() -> str:
        """Clear cart."""
        return clear_cart_api(token)

    return [
        food_items_tool,
        add_to_cart,
        get_cart,
        remove_from_cart,
        clear_cart
    ]


# =========================
# 🧠 HISTORY LOADER
# =========================
def load_history(user_id, session_id):
    data = session_manager.get_full_context(user_id, session_id)

    messages_raw = data.get("messages", [])
    summary = data.get("summary", "")

    if messages_raw:
        history = [
            HumanMessage(content=m["content"])
            if m["type"] == "human"
            else AIMessage(content=m["content"])
            for m in messages_raw
        ]
        return history, summary

    print("⚠️ Redis empty → loading from Mongo")

    mongo_msgs = get_conversation(user_id, session_id)

    if not mongo_msgs:
        return [], ""

    history = []
    formatted = []

    for msg in mongo_msgs:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
            formatted.append({"type": "human", "content": msg["content"]})
        else:
            history.append(AIMessage(content=msg["content"]))
            formatted.append({"type": "ai", "content": msg["content"]})

    # 🔥 FIXED summary crash
    # text = "\n".join([
    #     json.dumps(m["content"]) if isinstance(m["content"], (list, dict)) else str(m["content"])
    #     for m in formatted
    # ])

    summary = session_manager._generate_summary(formatted, "")

    session_manager.set_history(user_id, session_id, formatted)

    return history, summary


# =========================
# 🚀 MAIN AGENT
# =========================
def run_agent(user_id: str, session_id: str, user_message: str, token: str):

    try:
        total_start = time.time()

        # =========================
        # 1️⃣ HISTORY
        # =========================
        t0 = time.time()
        history, summary = load_history(user_id, session_id)
        print(f"⏱️ HISTORY LOAD TIME: {round(time.time() - t0, 4)}s")

        # =========================
        # 2️⃣ RAG
        # =========================
        t1 = time.time()
        chunks = fetch_relevant_chunks(user_message, limit=5)
        context = "\n".join(chunks) if chunks else "No relevant data found."
        print(f"⏱️ RAG FETCH TIME: {round(time.time() - t1, 4)}s")

        # =========================
        # 3️⃣ PROMPT BUILD
        # =========================
        t2 = time.time()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *history,
            HumanMessage(content=f"""
Conversation Summary:
{summary or "None"}

Knowledge Context:
{context}

User Query:
{user_message}
""")
        ]
        print(f"⏱️ PROMPT BUILD TIME: {round(time.time() - t2, 4)}s")

        # =========================
        # 4️⃣ AGENT INIT
        # =========================
        t3 = time.time()
        agent = create_react_agent(
            model=llm,
            tools=create_tools(token),
            prompt=None
        )
        print(f"⏱️ AGENT INIT TIME: {round(time.time() - t3, 4)}s")

        # =========================
        # 5️⃣ LLM EXECUTION
        # =========================
        t4 = time.time()
        response = agent.invoke({"messages": messages})
        print(f"⏱️ LLM + TOOL TIME: {round(time.time() - t4, 4)}s")

        # =========================
        # 6️⃣ RESPONSE PARSE
        # =========================
        t5 = time.time()

        ai_msg = response["messages"][-1]
        raw = ai_msg.content

        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, dict):
                parsed = [parsed]
        except:
            parsed = [{"type": "text", "text": str(raw)}]

        print(f"⏱️ RESPONSE PARSE TIME: {round(time.time() - t5, 4)}s")

        # =========================
        # 7️⃣ MEMORY STORE
        # =========================
        t6 = time.time()

        session_manager.append(user_id, session_id, HumanMessage(content=user_message))
        session_manager.append(user_id, session_id, AIMessage(content=str(parsed)))

        store_chat_async(user_id, session_id, user_message, str(parsed))

        print(f"⏱️ MEMORY STORE TIME: {round(time.time() - t6, 4)}s")

        # =========================
        # TOTAL TIME
        # =========================
        print("\n==============================")
        print(f"🚀 TOTAL LATENCY: {round(time.time() - total_start, 4)}s")
        print("==============================\n")

        return parsed

    except Exception as e:
        print("❌ AGENT ERROR:", str(e))
        print(traceback.format_exc())
        return [{"type": "text", "text": "Something went wrong"}]