from pymongo import MongoClient

try:
    client = MongoClient("mongodb://localhost:27017")
    client.admin.command('ping')
    print("✅ Connected to MongoDB")

    db = client["test_db"]
    col = db["test_col"]

    col.insert_one({"test": "hello"})
    print("✅ Insert successful")

except Exception as e:
    print("❌ Connection failed:", e)