from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import os

client = QdrantClient(host="localhost", port=6333)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

COLLECTION_NAME = "restaurant_knowledge"


# =========================
# 🔧 INIT COLLECTION
# =========================
def init_collection():
    try:
        collections = client.get_collections().collections
        existing = [col.name for col in collections]

        if COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print("✅ Qdrant collection created")
        else:
            print("✅ Qdrant collection exists")

    except Exception as e:
        print("❌ Qdrant init error:", e)


# =========================
# 📄 LOAD + CHUNK PDF
# =========================
def load_pdf_chunks(file_path="restaurant_RAG.pdf"):
    try:
        print("📂 Checking file path:", file_path)
        print("📂 Exists:", os.path.exists(file_path))

        if not os.path.exists(file_path):
            print("❌ File not found")
            return []

        reader = PdfReader(file_path)
        text = ""

        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()

            if page_text:
                print(f"📄 Page {i} extracted length:", len(page_text))
                text += page_text + "\n"
            else:
                print(f"⚠️ Page {i} returned no text")

        print("📄 Total extracted text length:", len(text))

        if not text.strip():
            print("❌ No text extracted from PDF")
            return []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        chunks = splitter.split_text(text)

        print(f"✅ Created {len(chunks)} chunks")

        return chunks

    except Exception as e:
        print("❌ PDF load error:", e)
        return []


# =========================
# 📥 STORE PDF IN QDRANT
# =========================
def store_pdf_embeddings(file_path="restaurant_RAG.pdf"):
    try:
        print("🚀 Starting ingestion...")

        # Ensure collection exists
        init_collection()

        # Check existing data
        existing_count = client.count(collection_name=COLLECTION_NAME).count
        print(f"📊 Existing vectors: {existing_count}")

        if existing_count > 0:
            print("⚠️ Data already present. Skipping ingestion.")
            return

        # Load chunks
        chunks = load_pdf_chunks(file_path)

        if not chunks:
            print("❌ No chunks found → stopping ingestion")
            return

        points = []

        for chunk in chunks:
            vector = model.encode(chunk).tolist()

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk,
                        "source": file_path,
                        "timestamp": str(datetime.utcnow())
                    }
                )
            )

        # Insert into Qdrant
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        # Verify insertion
        new_count = client.count(collection_name=COLLECTION_NAME).count

        print(f"✅ Stored {len(points)} chunks")
        print(f"📊 Total vectors now: {new_count}")

    except Exception as e:
        print("❌ Store PDF error:", e)


# =========================
# 🔍 FETCH RELEVANT CONTEXT
# =========================
def fetch_relevant_chunks(query: str, limit: int = 3):
    try:
        query_vector = model.encode(query).tolist()

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit
        )

        return [p.payload.get("text") for p in results.points]

    except Exception as e:
        print("❌ Qdrant fetch error:", e)
        return [] 