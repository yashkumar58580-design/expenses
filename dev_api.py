from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import sqlite3
import json

app = FastAPI(title="FinanceOS API - Dynamic", version="2.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# 📦 DATABASE SETUP
# ============================================================================

DB_NAME = "finance.db"

def init_db():
    """Database initialize karta hai - Pehli baar chalane pe"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'completed'
        )
    """)
    
    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            total_spent REAL DEFAULT 0,
            color TEXT NOT NULL
        )
    """)
    
    # Summary table (single row)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summary (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_balance REAL,
            monthly_income REAL,
            total_expenses REAL
        )
    """)
    
    # Check if summary exists, if not create it
    cursor.execute("SELECT COUNT(*) FROM summary")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO summary (id, total_balance, monthly_income, total_expenses)
            VALUES (1, 50000.0, 0.0, 0.0)
        """)
    
    # Check if categories exist, if not add defaults
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("Food & Dining", 0, "#10b981"),
            ("Rent", 0, "#3b82f6"),
            ("Transportation", 0, "#f59e0b"),
            ("Entertainment", 0, "#8b5cf6"),
            ("Utilities", 0, "#ec4899"),
            ("Shopping", 0, "#06b6d4"),
        ]
        cursor.executemany(
            "INSERT INTO categories (name, total_spent, color) VALUES (?, ?, ?)",
            default_categories
        )
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

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

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_category_totals():
    """Categories ka total calculate karta hai transactions se"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Reset all categories to 0
    cursor.execute("UPDATE categories SET total_spent = 0")
    
    # Calculate totals from transactions (only negative amounts = expenses)
    cursor.execute("""
        SELECT category, SUM(ABS(amount)) as total
        FROM transactions
        WHERE amount < 0
        GROUP BY category
    """)
    
    for row in cursor.fetchall():
        cursor.execute(
            "UPDATE categories SET total_spent = ? WHERE name = ?",
            (row['total'], row['category'])
        )
    
    conn.commit()
    conn.close()

def calculate_summary():
    """Summary automatically calculate karta hai"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total expenses (negative amounts)
    cursor.execute("SELECT SUM(ABS(amount)) FROM transactions WHERE amount < 0")
    total_expenses = cursor.fetchone()[0] or 0
    
    # Total income (positive amounts)
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE amount > 0")
    total_income = cursor.fetchone()[0] or 0
    
    # Get current balance
    cursor.execute("SELECT total_balance FROM summary WHERE id = 1")
    current_balance = cursor.fetchone()[0] or 0
    
    # Update summary
    cursor.execute("""
        UPDATE summary 
        SET total_expenses = ?, monthly_income = ?
        WHERE id = 1
    """, (total_expenses, total_income))
    
    conn.commit()
    conn.close()

# ============================================================================
# 🏠 BASIC ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    tx_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    cat_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "message": "🎉 FinanceOS Dynamic Backend",
        "status": "running",
        "version": "2.0.0",
        "database": "SQLite",
        "transactions": tx_count,
        "categories": cat_count,
        "endpoints": {
            "GET": "/transactions, /categories, /summary",
            "POST": "/transactions, /categories",
            "PUT": "/transactions/{id}, /summary",
            "DELETE": "/transactions/{id}, /categories/{id}"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============================================================================
# 💰 TRANSACTIONS ENDPOINTS (CRUD)
# ============================================================================

@app.get("/transactions")
async def get_all_transactions():
    """Frontend ke liye complete data return karta hai"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get summary
    cursor.execute("SELECT * FROM summary WHERE id = 1")
    summary_row = cursor.fetchone()
    summary = {
        "totalBalance": summary_row['total_balance'],
        "monthlyIncome": summary_row['monthly_income'],
        "totalExpenses": summary_row['total_expenses'],
        "balanceTrend": [42000, 43200, 44100, summary_row['total_balance']],
        "incomeTrend": [11800, 12100, 12200, summary_row['monthly_income']],
        "expensesTrend": [8200, 8500, 8800, summary_row['total_expenses']]
    }
    
    # Get categories
    cursor.execute("SELECT name, total_spent as value, color FROM categories WHERE total_spent > 0")
    categories = [dict(row) for row in cursor.fetchall()]
    
    # Get recent transactions (last 10)
    cursor.execute("""
        SELECT id, description, amount, date, category, status 
        FROM transactions 
        ORDER BY date DESC, id DESC 
        LIMIT 10
    """)
    transactions = [dict(row) for row in cursor.fetchall()]
    
    # Monthly trends (simplified - last 4 months)
    monthly_trends = [
        {"month": "Jan", "income": summary_row['monthly_income'] * 0.9, "expenses": summary_row['total_expenses'] * 0.9},
        {"month": "Feb", "income": summary_row['monthly_income'] * 0.95, "expenses": summary_row['total_expenses'] * 0.95},
        {"month": "Mar", "income": summary_row['monthly_income'] * 0.98, "expenses": summary_row['total_expenses'] * 0.98},
        {"month": "Apr", "income": summary_row['monthly_income'], "expenses": summary_row['total_expenses']}
    ]
    
    conn.close()
    
    return {
        "summary": summary,
        "categorySpending": categories,
        "monthlyTrends": monthly_trends,
        "recentTransactions": transactions
    }

@app.post("/transactions")
async def add_transaction(transaction: Transaction):
    """Naya transaction add karta hai"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO transactions (description, amount, date, category, status)
        VALUES (?, ?, ?, ?, ?)
    """, (transaction.description, transaction.amount, transaction.date, 
          transaction.category, transaction.status))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Recalculate totals
    calculate_category_totals()
    calculate_summary()
    
    return {"message": "Transaction added!", "id": new_id}

@app.get("/transactions/list")
async def get_transaction_list():
    """Saare transactions ki simple list"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions

@app.put("/transactions/{transaction_id}")
async def update_transaction(transaction_id: int, transaction: TransactionUpdate):
    """Existing transaction update karta hai"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Build update query
    updates = []
    values = []
    if transaction.description is not None:
        updates.append("description = ?")
        values.append(transaction.description)
    if transaction.amount is not None:
        updates.append("amount = ?")
        values.append(transaction.amount)
    if transaction.date is not None:
        updates.append("date = ?")
        values.append(transaction.date)
    if transaction.category is not None:
        updates.append("category = ?")
        values.append(transaction.category)
    if transaction.status is not None:
        updates.append("status = ?")
        values.append(transaction.status)
    
    if updates:
        values.append(transaction_id)
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    
    # Recalculate
    calculate_category_totals()
    calculate_summary()
    
    return {"message": "Transaction updated!"}

@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int):
    """Transaction delete karta hai"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    conn.commit()
    conn.close()
    
    # Recalculate
    calculate_category_totals()
    calculate_summary()
    
    return {"message": "Transaction deleted!"}

# ============================================================================
# 📊 CATEGORIES ENDPOINTS
# ============================================================================

@app.get("/categories")
async def get_categories():
    """Saari categories list"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories

@app.post("/categories")
async def add_category(category: Category):
    """Nayi category add karta hai"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO categories (name, color, total_spent)
            VALUES (?, ?, 0)
        """, (category.name, category.color))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return {"message": "Category added!", "id": new_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Category already exists")

@app.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    """Category delete karta hai"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Category not found")
    
    conn.commit()
    conn.close()
    return {"message": "Category deleted!"}

# ============================================================================
# 💼 SUMMARY ENDPOINTS
# ============================================================================

@app.get("/summary")
async def get_summary():
    """Current summary"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM summary WHERE id = 1")
    summary = dict(cursor.fetchone())
    conn.close()
    return summary

@app.put("/summary")
async def update_summary(summary: SummaryUpdate):
    """Summary manually update karta hai"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    if summary.total_balance is not None:
        updates.append("total_balance = ?")
        values.append(summary.total_balance)
    if summary.monthly_income is not None:
        updates.append("monthly_income = ?")
        values.append(summary.monthly_income)
    if summary.total_expenses is not None:
        updates.append("total_expenses = ?")
        values.append(summary.total_expenses)
    
    if updates:
        values.append(1)  # id = 1
        query = f"UPDATE summary SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return {"message": "Summary updated!"}

# ============================================================================
# 🔄 UTILITY ENDPOINTS
# ============================================================================

@app.post("/recalculate")
async def recalculate_all():
    """Sab kuch recalculate karta hai"""
    calculate_category_totals()
    calculate_summary()
    return {"message": "All totals recalculated!"}

@app.delete("/reset")
async def reset_database():
    """⚠️ DATABASE RESET - Sab data delete ho jayega!"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM categories")
    cursor.execute("UPDATE summary SET total_balance = 50000, monthly_income = 0, total_expenses = 0 WHERE id = 1")
    
    conn.commit()
    conn.close()
    
    # Reinitialize with defaults
    init_db()
    
    return {"message": "⚠️ Database reset complete!"}


if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 FinanceOS Dynamic Backend Starting...")
    print("=" * 70)
    print("💾 Database: SQLite (finance.db)")
    print("📊 Features: Full CRUD operations")
    print("=" * 70)
    print("🌐 API: http://127.0.0.1:8000")
    print("📚 Docs: http://127.0.0.1:8000/docs")
    print("=" * 70)
    print("\n🎯 Quick Commands:")
    print("   POST /transactions       - Add new transaction")
    print("   PUT /transactions/{id}   - Update transaction")
    print("   DELETE /transactions/{id} - Delete transaction")
    print("   POST /categories         - Add new category")
    print("   PUT /summary             - Update balance/income")
    print("=" * 70)
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
