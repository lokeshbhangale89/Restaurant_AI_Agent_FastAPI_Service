from app.memory.memory_store import store_pdf_embeddings

if __name__ == "__main__":
    print("📥 Running PDF ingestion...")
    store_pdf_embeddings("restaurant_RAG.pdf")
    print("✅ Ingestion completed")