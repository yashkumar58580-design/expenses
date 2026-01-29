from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import os
import json

app = FastAPI(title="Expenses API - INR (MongoDB)", version="2.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# 📦 MONGODB DATABASE SETUP
# ============================================================================

# Get MongoDB URI from environment variable
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "expenses_db"

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    # Collections
    transactions_collection = db["transactions"]
    categories_collection = db["categories"]
    summary_collection = db["summary"]
    
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")

def init_db():
    """Database initialize karta hai - Fresh start with zero data"""
    
    # Check if summary exists, if not create it with ZERO values
    if summary_collection.count_documents({}) == 0:
        summary_collection.insert_one({
            "total_balance": 0.0,
            "monthly_income": 0.0,
            "total_expenses": 0.0
        })
        print("✅ Summary initialized!")
    
    # Check if categories exist, if not add defaults
    if categories_collection.count_documents({}) == 0:
        default_categories = [
            {"name": "Food & Dining", "total_spent": 0, "color": "#10b981"},
            {"name": "Rent", "total_spent": 0, "color": "#3b82f6"},
            {"name": "Transportation", "total_spent": 0, "color": "#f59e0b"},
            {"name": "Entertainment", "total_spent": 0, "color": "#8b5cf6"},
            {"name": "Utilities", "total_spent": 0, "color": "#ec4899"},
            {"name": "Shopping", "total_spent": 0, "color": "#06b6d4"},
            {"name": "Health", "total_spent": 0, "color": "#f87171"},
            {"name": "Education", "total_spent": 0, "color": "#facc15"},
            {"name": "Income", "total_spent": 0, "color": "#10b981"},
        ]
        categories_collection.insert_many(default_categories)
        print("✅ Categories initialized!")
    
    print("✅ Database initialized with ZERO data!")

# Initialize database on startup
init_db()

# ============================================================================
# 📋 PYDANTIC MODELS (Request/Response schemas)
# ============================================================================

class Transaction(BaseModel):
    description: str
    amount: float
    date: str
    category: str
    status: str = "completed"

class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

class Category(BaseModel):
    name: str
    color: str

class SummaryUpdate(BaseModel):
    total_balance: Optional[float] = None
    monthly_income: Optional[float] = None
    total_expenses: Optional[float] = None

# ============================================================================
# 🔧 HELPER FUNCTIONS
# ============================================================================

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict"""
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

def calculate_category_totals():
    """Categories ka total calculate karta hai transactions se"""
    
    # Reset all categories to 0
    categories_collection.update_many({}, {"$set": {"total_spent": 0}})
    
    # Calculate totals from transactions (only negative amounts = expenses)
    pipeline = [
        {"$match": {"amount": {"$lt": 0}}},
        {"$group": {
            "_id": "$category",
            "total": {"$sum": {"$abs": "$amount"}}
        }}
    ]
    
    category_totals = list(transactions_collection.aggregate(pipeline))
    
    for item in category_totals:
        categories_collection.update_one(
            {"name": item["_id"]},
            {"$set": {"total_spent": item["total"]}}
        )

def calculate_summary():
    """Summary automatically calculate karta hai"""
    
    # Total expenses (negative amounts)
    pipeline_expenses = [
        {"$match": {"amount": {"$lt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": {"$abs": "$amount"}}}}
    ]
    expenses_result = list(transactions_collection.aggregate(pipeline_expenses))
    total_expenses = expenses_result[0]["total"] if expenses_result else 0
    
    # Total income (positive amounts)
    pipeline_income = [
        {"$match": {"amount": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    income_result = list(transactions_collection.aggregate(pipeline_income))
    total_income = income_result[0]["total"] if income_result else 0
    
    # Get current balance
    summary = summary_collection.find_one({})
    current_balance = summary.get("total_balance", 0) if summary else 0
    
    # Update summary
    summary_collection.update_one(
        {},
        {
            "$set": {
                "total_expenses": total_expenses,
                "monthly_income": total_income
            }
        }
    )

# ============================================================================
# 🏠 BASIC ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    tx_count = transactions_collection.count_documents({})
    cat_count = categories_collection.count_documents({})
    
    summary = summary_collection.find_one({})
    expenses = summary.get("total_expenses", 0) if summary else 0
    
    pending = transactions_collection.count_documents({"status": "pending"})
    
    return {
        "message": "🎉 Expenses Backend (INR) is Live!",
        "status": "running",
        "version": "2.0.0 INR - Full Featured (MongoDB)",
        "currency": "₹ INR",
        "database": "MongoDB",
        "app_name": "Expenses - Financial Intelligence System",
        "statistics": {
            "transactions": tx_count,
            "categories": cat_count,
            "pending_transactions": pending,
            "total_expenses": f"₹{expenses:,.2f}"
        },
        "endpoints": {
            "transactions": {
                "GET": "/transactions - Get all data for frontend",
                "POST": "/transactions - Add new transaction",
                "PUT": "/transactions/{id} - Update transaction",
                "DELETE": "/transactions/{id} - Delete transaction",
                "GET_LIST": "/transactions/list - Simple list",
                "SEARCH": "/transactions/search - Advanced search",
                "DATE_RANGE": "/transactions/date-range - Filter by dates",
                "BY_CATEGORY": "/transactions/category/{name} - Filter by category"
            },
            "analytics": {
                "MONTHLY": "/analytics/monthly - Month-wise breakdown",
                "CATEGORY": "/analytics/category-wise - Category statistics",
                "DAILY": "/analytics/daily - Last 30 days pattern",
                "TOP": "/analytics/top-expenses - Highest expenses",
                "SUMMARY": "/analytics/summary - Complete analytics"
            },
            "export": {
                "CSV": "/export/csv - Export as CSV",
                "JSON": "/export/json - Export as JSON"
            },
            "dashboard": {
                "STATS": "/dashboard/stats - Complete dashboard data",
                "QUICK": "/stats/quick - Quick stats for header"
            },
            "categories": {
                "GET": "/categories - List all",
                "POST": "/categories - Add new",
                "DELETE": "/categories/{id} - Delete"
            },
            "utilities": {
                "RESET": "DELETE /reset - Clear all data",
                "RECALCULATE": "POST /recalculate - Recalculate totals",
                "HEALTH": "GET /health - Health check"
            }
        },
        "features": [
            "✅ Full CRUD Operations",
            "✅ Advanced Search & Filters",
            "✅ Analytics & Statistics",
            "✅ Date Range Filtering",
            "✅ Category Management",
            "✅ Export (CSV/JSON)",
            "✅ Dashboard Stats",
            "✅ Monthly/Daily Breakdowns",
            "✅ Database Reset",
            "✅ MongoDB Cloud Database"
        ]
    }

@app.get("/health")
async def health():
    try:
        client.admin.command('ping')
        return {
            "status": "healthy", 
            "database": "connected",
            "timestamp": datetime.now().isoformat(), 
            "currency": "INR",
            "app": "Expenses"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")

# ============================================================================
# 💰 TRANSACTIONS ENDPOINTS (CRUD)
# ============================================================================

@app.get("/transactions")
async def get_all_transactions():
    """Frontend ke liye complete data return karta hai"""
    
    # Get summary
    summary_row = summary_collection.find_one({})
    
    if not summary_row:
        balance = income = expenses = 0
    else:
        balance = summary_row.get('total_balance', 0)
        income = summary_row.get('monthly_income', 0)
        expenses = summary_row.get('total_expenses', 0)
    
    # Create trends (last 4 months simulation)
    summary = {
        "totalBalance": balance,
        "monthlyIncome": income,
        "totalExpenses": expenses,
        "balanceTrend": [
            max(0, balance * 0.8),
            max(0, balance * 0.9),
            max(0, balance * 0.95),
            balance
        ],
        "incomeTrend": [
            max(0, income * 0.8),
            max(0, income * 0.9),
            max(0, income * 0.95),
            income
        ],
        "expensesTrend": [
            max(0, expenses * 0.8),
            max(0, expenses * 0.9),
            max(0, expenses * 0.95),
            expenses
        ]
    }
    
    # Get categories with non-zero spending
    categories = list(categories_collection.find({"total_spent": {"$gt": 0}}))
    categories = [{"name": c["name"], "value": c["total_spent"], "color": c["color"]} for c in categories]
    
    # If no categories, return default empty categories
    if not categories:
        all_cats = list(categories_collection.find({}))
        categories = [{"name": c["name"], "value": c.get("total_spent", 0), "color": c["color"]} for c in all_cats]
    
    # Get recent transactions (last 20)
    transactions = list(transactions_collection.find().sort([("date", -1), ("_id", -1)]).limit(20))
    transactions = [serialize_doc(tx) for tx in transactions]
    
    # Monthly trends
    monthly_trends = [
        {"month": "Jan", "income": max(0, income * 0.8), "expenses": max(0, expenses * 0.8)},
        {"month": "Feb", "income": max(0, income * 0.9), "expenses": max(0, expenses * 0.9)},
        {"month": "Mar", "income": max(0, income * 0.95), "expenses": max(0, expenses * 0.95)},
        {"month": "Apr", "income": income, "expenses": expenses}
    ]
    
    return {
        "summary": summary,
        "categorySpending": categories,
        "monthlyTrends": monthly_trends,
        "recentTransactions": transactions
    }

@app.post("/transactions")
async def add_transaction(transaction: Transaction):
    """Naya transaction add karta hai"""
    
    tx_dict = transaction.dict()
    result = transactions_collection.insert_one(tx_dict)
    
    # Recalculate totals
    calculate_category_totals()
    calculate_summary()
    
    return {
        "message": "✅ Transaction added successfully!", 
        "id": str(result.inserted_id),
        "transaction": transaction.dict()
    }

@app.get("/transactions/list")
async def get_transaction_list():
    """Saare transactions ki simple list"""
    transactions = list(transactions_collection.find().sort([("date", -1), ("_id", -1)]))
    return [serialize_doc(tx) for tx in transactions]

@app.put("/transactions/{transaction_id}")
async def update_transaction(transaction_id: str, transaction: TransactionUpdate):
    """Existing transaction update karta hai"""
    
    try:
        obj_id = ObjectId(transaction_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")
    
    # Check if exists
    existing = transactions_collection.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Build update data
    update_data = {k: v for k, v in transaction.dict().items() if v is not None}
    
    if update_data:
        transactions_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
    
    # Recalculate
    calculate_category_totals()
    calculate_summary()
    
    return {"message": "✅ Transaction updated!", "id": transaction_id}

@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    """Transaction delete karta hai"""
    
    try:
        obj_id = ObjectId(transaction_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")
    
    result = transactions_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Recalculate
    calculate_category_totals()
    calculate_summary()
    
    return {"message": "✅ Transaction deleted!", "id": transaction_id}

# ============================================================================
# 📊 CATEGORIES ENDPOINTS
# ============================================================================

@app.get("/categories")
async def get_categories():
    """Saari categories list"""
    categories = list(categories_collection.find().sort("name", 1))
    return [serialize_doc(cat) for cat in categories]

@app.post("/categories")
async def add_category(category: Category):
    """Nayi category add karta hai"""
    
    # Check if already exists
    existing = categories_collection.find_one({"name": category.name})
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    cat_dict = category.dict()
    cat_dict["total_spent"] = 0
    result = categories_collection.insert_one(cat_dict)
    
    return {"message": "✅ Category added!", "id": str(result.inserted_id)}

@app.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    """Category delete karta hai"""
    
    try:
        obj_id = ObjectId(category_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    result = categories_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "✅ Category deleted!", "id": category_id}

# ============================================================================
# 💼 SUMMARY ENDPOINTS
# ============================================================================

@app.get("/summary")
async def get_summary():
    """Current summary"""
    summary = summary_collection.find_one({})
    if not summary:
        return {
            "total_balance": 0.0,
            "monthly_income": 0.0,
            "total_expenses": 0.0
        }
    return serialize_doc(summary)

@app.put("/summary")
async def update_summary(summary: SummaryUpdate):
    """Summary manually update karta hai (Balance set karne ke liye)"""
    
    update_data = {k: v for k, v in summary.dict().items() if v is not None}
    
    if update_data:
        summary_collection.update_one({}, {"$set": update_data})
    
    return {"message": "✅ Summary updated!"}

# ============================================================================
# 📊 ANALYTICS & STATS ENDPOINTS
# ============================================================================

@app.get("/analytics/monthly")
async def get_monthly_analytics():
    """Month-wise breakdown of income and expenses"""
    
    pipeline = [
        {
            "$addFields": {
                "month": {"$substr": ["$date", 0, 7]}
            }
        },
        {
            "$group": {
                "_id": "$month",
                "income": {
                    "$sum": {
                        "$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]
                    }
                },
                "expenses": {
                    "$sum": {
                        "$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]
                    }
                }
            }
        },
        {"$sort": {"_id": -1}},
        {"$limit": 12}
    ]
    
    monthly_data = list(transactions_collection.aggregate(pipeline))
    monthly_data = [{"month": item["_id"], "income": item["income"], "expenses": item["expenses"]} for item in monthly_data]
    
    return {
        "monthly_breakdown": monthly_data,
        "total_months": len(monthly_data)
    }

@app.get("/analytics/category-wise")
async def get_category_analytics():
    """Category-wise detailed breakdown"""
    
    pipeline = [
        {"$match": {"amount": {"$lt": 0}}},
        {
            "$group": {
                "_id": "$category",
                "transaction_count": {"$sum": 1},
                "total_amount": {"$sum": {"$abs": "$amount"}},
                "avg_amount": {"$avg": {"$abs": "$amount"}},
                "min_amount": {"$min": {"$abs": "$amount"}},
                "max_amount": {"$max": {"$abs": "$amount"}}
            }
        },
        {"$sort": {"total_amount": -1}}
    ]
    
    category_stats = list(transactions_collection.aggregate(pipeline))
    category_stats = [{
        "category": item["_id"],
        "transaction_count": item["transaction_count"],
        "total_amount": item["total_amount"],
        "avg_amount": item["avg_amount"],
        "min_amount": item["min_amount"],
        "max_amount": item["max_amount"]
    } for item in category_stats]
    
    return {
        "category_statistics": category_stats,
        "total_categories": len(category_stats)
    }

@app.get("/analytics/daily")
async def get_daily_spending():
    """Daily spending pattern for last 30 days"""
    
    # Calculate date 30 days ago
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    pipeline = [
        {"$match": {"date": {"$gte": thirty_days_ago}}},
        {
            "$group": {
                "_id": "$date",
                "expenses": {
                    "$sum": {
                        "$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]
                    }
                },
                "income": {
                    "$sum": {
                        "$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]
                    }
                },
                "transaction_count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": -1}}
    ]
    
    daily_data = list(transactions_collection.aggregate(pipeline))
    daily_data = [{
        "date": item["_id"],
        "expenses": item["expenses"],
        "income": item["income"],
        "transaction_count": item["transaction_count"]
    } for item in daily_data]
    
    return {
        "daily_breakdown": daily_data,
        "period": "Last 30 days"
    }

@app.get("/analytics/top-expenses")
async def get_top_expenses():
    """Top 10 highest expenses"""
    
    transactions = list(
        transactions_collection.find({"amount": {"$lt": 0}})
        .sort("amount", 1)
        .limit(10)
    )
    
    top_expenses = []
    for tx in transactions:
        top_expenses.append({
            "id": str(tx["_id"]),
            "description": tx["description"],
            "amount": abs(tx["amount"]),
            "date": tx["date"],
            "category": tx["category"]
        })
    
    return {
        "top_expenses": top_expenses,
        "count": len(top_expenses)
    }

@app.get("/analytics/summary")
async def get_analytics_summary():
    """Complete analytics summary"""
    
    # Total stats
    all_tx = list(transactions_collection.find({}))
    
    total_transactions = len(all_tx)
    total_expenses = sum(abs(tx["amount"]) for tx in all_tx if tx["amount"] < 0)
    total_income = sum(tx["amount"] for tx in all_tx if tx["amount"] > 0)
    avg_expense = total_expenses / total_transactions if total_transactions > 0 else 0
    
    stats = {
        "total_transactions": total_transactions,
        "total_expenses": total_expenses,
        "total_income": total_income,
        "avg_expense": avg_expense
    }
    
    # This month
    current_month = datetime.now().strftime("%Y-%m")
    this_month_tx = [tx for tx in all_tx if tx["date"].startswith(current_month)]
    
    this_month = {
        "transactions_this_month": len(this_month_tx),
        "expenses_this_month": sum(abs(tx["amount"]) for tx in this_month_tx if tx["amount"] < 0),
        "income_this_month": sum(tx["amount"] for tx in this_month_tx if tx["amount"] > 0)
    }
    
    # Last month
    last_month_date = (datetime.now() - timedelta(days=30))
    last_month = last_month_date.strftime("%Y-%m")
    last_month_tx = [tx for tx in all_tx if tx["date"].startswith(last_month)]
    
    expenses_last_month = sum(abs(tx["amount"]) for tx in last_month_tx if tx["amount"] < 0)
    
    last_month_data = {"expenses_last_month": expenses_last_month}
    
    # Calculate change percentage
    if expenses_last_month > 0:
        change = ((this_month["expenses_this_month"] - expenses_last_month) / expenses_last_month) * 100
    else:
        change = 0
    
    return {
        "all_time": stats,
        "this_month": this_month,
        "last_month": last_month_data,
        "month_over_month_change": f"{change:.2f}%"
    }

# ============================================================================
# 🔍 SEARCH & FILTER ENDPOINTS
# ============================================================================

@app.get("/transactions/search")
async def search_transactions(
    query: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None
):
    """Advanced search with multiple filters"""
    
    filter_query = {}
    
    if query:
        filter_query["$or"] = [
            {"description": {"$regex": query, "$options": "i"}},
            {"category": {"$regex": query, "$options": "i"}}
        ]
    
    if category:
        filter_query["category"] = category
    
    if status:
        filter_query["status"] = status
    
    if date_from:
        filter_query.setdefault("date", {})["$gte"] = date_from
    
    if date_to:
        filter_query.setdefault("date", {})["$lte"] = date_to
    
    if min_amount is not None or max_amount is not None:
        amount_filter = {}
        if min_amount is not None:
            # For expenses (negative) and income (positive)
            amount_filter["$gte"] = -max(min_amount, 0) if min_amount < 0 else min_amount
        if max_amount is not None:
            amount_filter["$lte"] = -min(max_amount, 0) if max_amount < 0 else max_amount
        
        if amount_filter:
            filter_query["amount"] = amount_filter
    
    results = list(transactions_collection.find(filter_query).sort([("date", -1), ("_id", -1)]))
    results = [serialize_doc(tx) for tx in results]
    
    return {
        "results": results,
        "count": len(results),
        "filters_applied": {
            "query": query,
            "category": category,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
            "min_amount": min_amount,
            "max_amount": max_amount
        }
    }

@app.get("/transactions/date-range")
async def get_transactions_by_date_range(date_from: str, date_to: str):
    """Get transactions within date range"""
    
    transactions = list(
        transactions_collection.find({
            "date": {"$gte": date_from, "$lte": date_to}
        }).sort([("date", -1), ("_id", -1)])
    )
    transactions = [serialize_doc(tx) for tx in transactions]
    
    # Calculate summary for this range
    total_expenses = sum(abs(tx["amount"]) for tx in transactions if tx["amount"] < 0)
    total_income = sum(tx["amount"] for tx in transactions if tx["amount"] > 0)
    
    summary = {
        "total_expenses": total_expenses,
        "total_income": total_income,
        "transaction_count": len(transactions)
    }
    
    return {
        "date_range": {
            "from": date_from,
            "to": date_to
        },
        "transactions": transactions,
        "summary": summary
    }

@app.get("/transactions/category/{category_name}")
async def get_transactions_by_category(category_name: str):
    """Get all transactions for a specific category"""
    
    transactions = list(
        transactions_collection.find({"category": category_name})
        .sort([("date", -1), ("_id", -1)])
    )
    transactions = [serialize_doc(tx) for tx in transactions]
    
    # Calculate category total
    expense_txs = [tx for tx in transactions if tx["amount"] < 0]
    count = len(expense_txs)
    total = sum(abs(tx["amount"]) for tx in expense_txs)
    
    stats = {
        "count": count,
        "total": total
    }
    
    return {
        "category": category_name,
        "transactions": transactions,
        "statistics": stats
    }

# ============================================================================
# 📤 EXPORT ENDPOINTS
# ============================================================================

@app.get("/export/csv")
async def export_to_csv():
    """Export all transactions as CSV format"""
    
    transactions = list(transactions_collection.find().sort("date", -1))
    
    # Create CSV data
    csv_lines = ["ID,Description,Amount,Date,Category,Status"]
    for tx in transactions:
        csv_lines.append(
            f"{tx['_id']},{tx['description']},{tx['amount']},{tx['date']},{tx['category']},{tx['status']}"
        )
    
    csv_content = "\n".join(csv_lines)
    
    return {
        "format": "CSV",
        "content": csv_content,
        "total_records": len(transactions),
        "filename": f"expenses_export_{datetime.now().strftime('%Y%m%d')}.csv"
    }

@app.get("/export/json")
async def export_to_json():
    """Export all data as JSON"""
    
    # Get all transactions
    transactions = list(transactions_collection.find().sort("date", -1))
    transactions = [serialize_doc(tx) for tx in transactions]
    
    # Get all categories
    categories = list(categories_collection.find())
    categories = [serialize_doc(cat) for cat in categories]
    
    # Get summary
    summary = summary_collection.find_one({})
    summary = serialize_doc(summary) if summary else {}
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "app": "Expenses - Financial Intelligence System",
        "currency": "INR",
        "database": "MongoDB",
        "summary": summary,
        "transactions": transactions,
        "categories": categories,
        "total_records": len(transactions)
    }
    
    return export_data

# ============================================================================
# 📊 DASHBOARD STATS ENDPOINT
# ============================================================================

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Complete dashboard statistics"""
    
    all_tx = list(transactions_collection.find({}))
    
    # Overall stats
    total_transactions = len(all_tx)
    active_categories = len(set(tx["category"] for tx in all_tx))
    total_expenses = sum(abs(tx["amount"]) for tx in all_tx if tx["amount"] < 0)
    total_income = sum(tx["amount"] for tx in all_tx if tx["amount"] > 0)
    last_transaction_date = max((tx["date"] for tx in all_tx), default="N/A")
    
    overall = {
        "total_transactions": total_transactions,
        "active_categories": active_categories,
        "total_expenses": total_expenses,
        "total_income": total_income,
        "last_transaction_date": last_transaction_date
    }
    
    # Today's stats
    today = datetime.now().strftime("%Y-%m-%d")
    today_tx = [tx for tx in all_tx if tx["date"] == today]
    
    today_data = {
        "transactions_today": len(today_tx),
        "expenses_today": sum(abs(tx["amount"]) for tx in today_tx if tx["amount"] < 0)
    }
    
    # This week
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_tx = [tx for tx in all_tx if tx["date"] >= week_ago]
    
    this_week = {
        "transactions_this_week": len(week_tx),
        "expenses_this_week": sum(abs(tx["amount"]) for tx in week_tx if tx["amount"] < 0)
    }
    
    # Pending transactions
    pending_count = sum(1 for tx in all_tx if tx.get("status") == "pending")
    pending = {"pending_count": pending_count}
    
    return {
        "overall": overall,
        "today": today_data,
        "this_week": this_week,
        "pending": pending,
        "generated_at": datetime.now().isoformat()
    }

# ============================================================================
# 🔄 UTILITY ENDPOINTS
# ============================================================================

@app.post("/recalculate")
async def recalculate_all():
    """Sab kuch recalculate karta hai"""
    calculate_category_totals()
    calculate_summary()
    return {"message": "✅ All totals recalculated!"}

@app.delete("/reset")
async def reset_database():
    """⚠️ DATABASE RESET - Sab data delete ho jayega!"""
    
    # Delete all transactions
    transactions_collection.delete_many({})
    
    # Reset summary to zero
    summary_collection.update_one(
        {},
        {
            "$set": {
                "total_balance": 0,
                "monthly_income": 0,
                "total_expenses": 0
            }
        }
    )
    
    # Reset all category totals to zero
    categories_collection.update_many({}, {"$set": {"total_spent": 0}})
    
    return {
        "message": "⚠️ Database reset complete! All transactions deleted.",
        "total_expenses": "₹0.00",
        "transactions": 0
    }

@app.get("/stats/quick")
async def get_quick_stats():
    """Quick stats for header/dashboard"""
    
    tx_count = transactions_collection.count_documents({})
    
    summary = summary_collection.find_one({})
    expenses = summary.get("total_expenses", 0) if summary else 0
    
    pending = transactions_collection.count_documents({"status": "pending"})
    
    return {
        "total_transactions": tx_count,
        "total_expenses": expenses,
        "pending_transactions": pending,
        "formatted_expenses": f"₹{expenses:,.2f}"
    }

# ============================================================================
# 🚀 STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("=" * 80)
    print("🚀 Expenses Backend (INR) Starting...")
    print("=" * 80)
    print("📱 App Name: Expenses - Financial Intelligence System")
    print("💾 Database: MongoDB Cloud")
    print("💰 Currency: ₹ INR (Indian Rupees)")
    print("📊 Starting Expenses: ₹0.00")
    print("=" * 80)
    print("🎯 Features Available:")
    print("   ✅ Full CRUD Operations (Create, Read, Update, Delete)")
    print("   ✅ Advanced Search & Filters")
    print("   ✅ Analytics & Statistics")
    print("   ✅ Monthly/Daily Breakdowns")
    print("   ✅ Category Management")
    print("   ✅ Export (CSV/JSON)")
    print("   ✅ Dashboard Stats")
    print("   ✅ Date Range Filtering")
    print("   ✅ Database Reset")
    print("   ✅ Cloud MongoDB Database")
    print("=" * 80)

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 8000))
    is_production = os.getenv("RENDER") is not None
    
    if is_production:
        print(f"\n🌐 Production Server on port {port}")
    else:
        print(f"\n🌐 Local Development Server on port {port}")
        print("📚 Docs: http://127.0.0.1:8000/docs")
    
    print("=" * 80)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        reload=not is_production
    )
