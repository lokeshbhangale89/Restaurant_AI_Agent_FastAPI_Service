from app.agent import run_agent
from app.memory.mongo_store import get_or_create_session
from app.memory.memory_store import init_collection

# Initialize vector DB (only first time)
# init_collection()

USER_ID = "test_user_123"
DUMMY_TOKEN = "dummy_jwt_token"

# Create / get session
session_id = get_or_create_session(USER_ID)

print("🤖 AI Agent Test Started (type 'exit' to stop)\n")

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    response = run_agent(
        user_id=USER_ID,
        session_id=session_id,
        user_message=user_input,
        token=DUMMY_TOKEN
    )

    print("AI:", response)