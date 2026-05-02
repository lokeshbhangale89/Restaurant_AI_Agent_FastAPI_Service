# 🍽️ Restaurant AI Assistant

An AI-powered assistant integrated with a full-stack restaurant system to enable:

- 🍛 Smart menu discovery  
- 🤖 AI-based recommendations  
- 🛒 Cart operations (Add / Remove / View / Clear)  
- 🧠 Context-aware conversations (Memory + RAG)

---

## 🎬 Demo

🎥 **Full Demo Video**  
https://drive.google.com/drive/folders/1GJin8A_ZaNECMS8FIgd8nQST_hsT0pgD?usp=sharing

---

## 🏗️ Architecture Overview

This project follows a **microservice-based AI architecture**, where the AI service acts as an intelligent layer over backend APIs.

### 🔷 System Design

```
React Frontend (Chat UI)
        │
        ▼
Spring Boot Backend (Auth + Cart + Menu APIs)
        │
        ▼
FastAPI AI Service
        │
        ├── 🤖 LangGraph ReAct Agent
        │       ├── Intent Classification
        │       └── Tool Execution
        │
        ├── 🛠️ Tools Layer
        │       └── Menu & Cart APIs
        │
        ├── 🧠 Memory Layer
        │       ├── Redis (Recent + Summary)
        │       └── MongoDB (Persistent History)
        │
        ├── 📚 RAG Pipeline
        │       ├── Qdrant (Vector DB)
        │       └── Embeddings (MiniLM)
        │
        ▼
Gemini LLM (Response Generation)
```

---

## 🔁 Request Flow

1. User sends a message from the frontend (React UI)  
2. Spring Boot backend authenticates the request and forwards it to the FastAPI AI service  
3. FastAPI receives the request and starts processing  

4. **System Preparation**
   - Load conversation memory (Redis → MongoDB fallback)  
   - Fetch relevant RAG context from Qdrant  
   - Build final prompt (summary + context + user query)  

5. **Agent Execution (LangGraph)**
   - Classify user intent  
   - Decide if a tool call is required  

6. If required, agent calls backend APIs via tools (menu/cart operations)  

7. Gemini LLM generates the final response  

8. **Memory Update**
   - Redis → short-term memory + summary  
   - MongoDB → persistent chat history  

9. Final response is returned to the frontend  

---

## 🧠 Memory Strategy

| Layer   | Purpose |
|--------|--------|
| Redis  | Fast access (recent messages + summary) |
| MongoDB | Persistent chat history |

---

## 📚 RAG Pipeline

### Ingestion
```
PDF → Text → Chunking → Embeddings → Qdrant
```

### Runtime
```
User Query → Embedding → Similarity Search → Context Injection
```

---

## 🚀 Setup & Run

### 1️⃣ Clone Full Stack Project

```bash
git clone https://github.com/lokeshbhangale89/Restuarant_FullStack_App_JavaReact_AI_Assistant
cd Restuarant_FullStack_App_JavaReact_AI_Assistant
```

---

### 2️⃣ Start Backend + Frontend

```bash
cd SmartRestaurantEngine
./mvnw clean package
docker-compose up --build
```

✅ Backend and frontend will be running

---

### 3️⃣ Setup AI Service

```bash
git clone https://github.com/lokeshbhangale89/Restaurant_AI_Agent_FastAPI_Service.git
cd Restaurant_AI_Agent_FastAPI_Service
```

---

### Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Configure Environment

Create `.env` file:

```
GOOGLE_API_KEY=your_gemini_api_key
```

---

### Run AI Service

```bash
uvicorn app.main:app --reload
```

➡️ Runs on: http://localhost:8000

---

## 📄 Load RAG Data

Run:

```bash
python inject_RAG.py
```

This will:
- Read PDF
- Create embeddings
- Store in Qdrant

---

## 🔗 API

### POST `/chat`

#### Request
```json
{
  "user_id": "user123",
  "token": "auth_token",
  "message": "show me paneer dishes"
}
```

#### Response
```json
{
  "userId": "user123",
  "sessionId": "session-xyz",
  "message": [...]
}
```

---

## 🧪 Example Queries

- Show me menu and recommend something spicy
- How is biryani and add it to my cart
- I want something spicy and vegetarian, what do you recommend? 
- Tell me what conversation we had last time 
- what makes your restaurant special

---

## 👨‍💻 Author

**Lokesh Bhangale**

Feel free to connect with me to learn more about this project and my work.
Contact - lokeshbhangale89@gmail.com
