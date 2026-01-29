from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import os

app = FastAPI(title="Expenses API - INR (MongoDB)", version="2.0.0")

# ✅ CORS Setup: Frontend connection ke liye zaroori
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MONGODB CONNECTION (Optimized for Serverless)
# Vercel har request par naya process chalata hai, isliye connection handle karna zaroori hai
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "expenses_db"

client = None
db = None

def get_db():
    global client, db
    if db is None:
        try:
            # serverSelectionTimeoutMS use kiya hai taaki crash na ho agar DB slow ho
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            db = client[DATABASE_NAME]
            # Ping test
            client.admin.command('ping')
            print("✅ Connected to MongoDB Cloud!")
        except Exception as e:
            print(f"❌ Connection error: {e}")
            raise HTTPException(status_code=503, detail="Database connection failed")
    return db

# Collections (Get inside functions to ensure connection)
def get_collections():
    database = get_db()
    return {
        "tx_col": database["transactions"],
        "cat_col": database["categories"],
        "sum_col": database["summary"]
    }

# ============================================================================
# 📋 MODELS & HELPERS
# ============================================================================

class Transaction(BaseModel):
    description: str
    amount: float
    date: str
    category: str
    status: str = "completed"

def serialize_doc(doc):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

# ============================================================================
# 🏠 ENDPOINTS (Vercel ke hisaab se paths fix kiye hain)
# ============================================================================

@app.get("/")
@app.get("/api")
async def root():
    cols = get_collections()
    tx_count = cols["tx_col"].count_documents({})
    return {
        "message": "🎉 Expenses Backend is Live!",
        "stats": {"total_transactions": tx_count},
        "currency": "₹ INR"
    }

@app.get("/api/health")
async def health():
    cols = get_collections()
    cols["tx_col"].find_one({}) # Simple check
    return {"status": "healthy", "database": "connected"}

@app.get("/api/transactions")
async def get_all_transactions():
    cols = get_collections()
    
    # Get summary
    summary = cols["sum_col"].find_one({}) or {"total_balance": 0, "monthly_income": 0, "total_expenses": 0}
    
    # Get categories
    categories = list(cols["cat_col"].find({"total_spent": {"$gt": 0}}))
    categories = [{"name": c["name"], "value": c["total_spent"], "color": c["color"]} for c in categories]
    
    # Get recent (limit 20)
    txs = list(cols["tx_col"].find().sort([("date", -1), ("_id", -1)]).limit(20))
    txs = [serialize_doc(tx) for tx in txs]
    
    income = summary.get("monthly_income", 0)
    expenses = summary.get("total_expenses", 0)

    return {
        "summary": {
            "totalBalance": summary.get("total_balance", 0),
            "monthlyIncome": income,
            "totalExpenses": expenses,
            "balanceTrend": [0, 0, 0, summary.get("total_balance", 0)],
            "incomeTrend": [0, 0, 0, income],
            "expensesTrend": [0, 0, 0, expenses]
        },
        "categorySpending": categories,
        "recentTransactions": txs,
        "monthlyTrends": [{"month": "Current", "income": income, "expenses": expenses}]
    }

@app.post("/api/transactions")
async def add_transaction(transaction: Transaction):
    cols = get_collections()
    tx_dict = transaction.dict()
    result = cols["tx_col"].insert_one(tx_dict)
    
    # Simple Recalculate (Serverless friendly)
    all_txs = list(cols["tx_col"].find({}))
    total_expenses = sum(abs(t["amount"]) for t in all_txs if t["amount"] < 0)
    total_income = sum(t["amount"] for t in all_txs if t["amount"] > 0)
    
    cols["sum_col"].update_one({}, {"$set": {
        "total_expenses": total_expenses,
        "monthly_income": total_income,
        "total_balance": total_income - total_expenses
    }}, upsert=True)
    
    return {"message": "✅ Added", "id": str(result.inserted_id)}

@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    cols = get_collections()
    cols["tx_col"].delete_one({"_id": ObjectId(transaction_id)})
    return {"message": "✅ Deleted"}

@app.delete("/api/reset")
async def reset_database():
    cols = get_collections()
    cols["tx_col"].delete_many({})
    cols["sum_col"].update_one({}, {"$set": {"total_balance": 0, "monthly_income": 0, "total_expenses": 0}}, upsert=True)
    return {"message": "⚠️ Reset complete"}

# Vercel ko batane ke liye ki app yahi hai
app = app