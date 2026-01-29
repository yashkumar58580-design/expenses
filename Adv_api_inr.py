from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import os

# ✅ FastAPI Instance
app = FastAPI(title="Expenses API - INR (MongoDB)", version="2.0.0")

# ✅ CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# 📦 MONGODB CONNECTION (Optimized for Serverless)
# ============================================================================
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "expenses_db"

# Connection check function (Serverless friendly)
def get_db():
    try:
        # serverSelectionTimeoutMS use kiya hai taaki crash na ho agar DB slow ho
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        # Ping test
        client.admin.command('ping')
        return db
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return None

# Collections Helper
def get_collections():
    database = get_db()
    if database is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {
        "tx_col": database["transactions"],
        "cat_col": database["categories"],
        "sum_col": database["summary"]
    }

# Serializer
def serialize_doc(doc):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

# ============================================================================
# 🏠 ENDPOINTS (Vercel ke liye /api/ prefix zaroori hai)
# ============================================================================

@app.get("/api")
async def root():
    return {
        "message": "🎉 Expenses Backend (INR) is Live!",
        "currency": "₹ INR",
        "app_name": "Expenses - Financial Intelligence System"
    }

@app.get("/api/health")
async def health():
    db = get_db()
    if db is not None:
        return {"status": "healthy", "database": "connected"}
    return {"status": "unhealthy", "database": "disconnected"}

@app.get("/api/transactions")
async def get_all_transactions():
    cols = get_collections()
    
    # Get summary
    summary_row = cols["sum_col"].find_one({}) or {"total_balance": 0, "monthly_income": 0, "total_expenses": 0}
    
    # Get categories with spending
    categories = list(cols["cat_col"].find({"total_spent": {"$gt": 0}}))
    category_list = [{"name": c["name"], "value": c["total_spent"], "color": c["color"]} for c in categories]
    
    # If no active categories, show all defaults
    if not category_list:
        all_cats = list(cols["cat_col"].find({}))
        category_list = [{"name": c["name"], "value": 0, "color": c["color"]} for c in all_cats]
    
    # Get recent (last 20)
    txs = list(cols["tx_col"].find().sort([("date", -1), ("_id", -1)]).limit(20))
    txs = [serialize_doc(tx) for tx in txs]
    
    balance = summary_row.get("total_balance", 0)
    income = summary_row.get("monthly_income", 0)
    expenses = summary_row.get("total_expenses", 0)

    return {
        "summary": {
            "totalBalance": balance,
            "monthlyIncome": income,
            "totalExpenses": expenses,
            "balanceTrend": [0, 0, 0, balance],
            "incomeTrend": [0, 0, 0, income],
            "expensesTrend": [0, 0, 0, expenses]
        },
        "categorySpending": category_list,
        "recentTransactions": txs,
        "monthlyTrends": [{"month": "Current", "income": income, "expenses": expenses}]
    }

# Pydantic Model
class Transaction(BaseModel):
    description: str
    amount: float
    date: str
    category: str
    status: str = "completed"

@app.post("/api/transactions")
async def add_transaction(transaction: Transaction):
    cols = get_collections()
    tx_dict = transaction.dict()
    result = cols["tx_col"].insert_one(tx_dict)
    
    # Quick Recalculate
    all_txs = list(cols["tx_col"].find({}))
    total_expenses = sum(abs(t["amount"]) for t in all_txs if t["amount"] < 0)
    total_income = sum(t["amount"] for t in all_txs if t["amount"] > 0)
    
    cols["sum_col"].update_one({}, {"$set": {
        "total_expenses": total_expenses,
        "monthly_income": total_income,
        "total_balance": total_income - total_expenses
    }}, upsert=True)
    
    return {"message": "✅ Transaction added!", "id": str(result.inserted_id)}

@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    cols = get_collections()
    try:
        cols["tx_col"].delete_one({"_id": ObjectId(transaction_id)})
        return {"message": "✅ Deleted"}
    except:
        raise HTTPException(status_code=400, detail="Invalid ID")

@app.delete("/api/reset")
async def reset_database():
    cols = get_collections()
    cols["tx_col"].delete_many({})
    cols["sum_col"].update_one({}, {"$set": {"total_balance": 0, "monthly_income": 0, "total_expenses": 0}}, upsert=True)
    return {"message": "⚠️ Reset complete"}

# Vercel entry point
app = app