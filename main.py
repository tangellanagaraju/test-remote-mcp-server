import sqlite3
import json
from datetime import datetime
from fastmcp import FastMCP

# ---------------------------------------------------------
# Load categories & subcategories from config.json
# ---------------------------------------------------------
with open("config.json", "r") as f:
    CONFIG = json.load(f)

CATEGORIES = CONFIG.get("categories", {})

# ---------------------------------------------------------
# Initialize MCP Server
# ---------------------------------------------------------
mcp = FastMCP(name="expense-tracker-sqlite")

# ---------------------------------------------------------
# SQLite setup
# ---------------------------------------------------------
DB_NAME = "expenses3.db"   # ⭐ NEW DB FILE NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

# Create table if not exists
with get_connection() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            description TEXT,
            date TEXT NOT NULL
        );
    """)
    conn.commit()

# ---------------------------------------------------------
# Validate Category/Subcategory
# ---------------------------------------------------------
def validate_category(category, subcategory=None):
    if category not in CATEGORIES:
        return False, f"Invalid category '{category}'. Allowed: {list(CATEGORIES.keys())}"

    if subcategory:
        if subcategory not in CATEGORIES[category]:
            return False, f"Invalid subcategory '{subcategory}' for '{category}'. Allowed: {CATEGORIES[category]}"

    return True, ""

# ---------------------------------------------------------
# 1. ADD EXPENSE
# ---------------------------------------------------------
@mcp.tool()
def add_expense(
    amount: float,
    category: str,
    subcategory: str = None,
    description: str = "",
    date: str = None
) -> dict:
    """
    Add an expense with manual DATE input.
    Example date: "2025-02-03"
    """

    # If date is not given, use today's date
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    # Validate categories
    ok, msg = validate_category(category, subcategory)
    if not ok:
        return {"error": msg}

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (amount, category, subcategory, description, date) VALUES (?, ?, ?, ?, ?)",
            (amount, category, subcategory, description, date)
        )
        conn.commit()

    return {"message": "Expense added successfully.", "expense_id": cursor.lastrowid}

# ---------------------------------------------------------
# 2. LIST EXPENSES
# ---------------------------------------------------------
@mcp.tool()
def list_expenses() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM expenses").fetchall()

    return {
        "expenses": [
            {
                "id": r[0],
                "amount": r[1],
                "category": r[2],
                "subcategory": r[3],
                "description": r[4],
                "date": r[5]
            }
            for r in rows
        ]
    }

# ---------------------------------------------------------
# 3. EDIT EXPENSE
# ---------------------------------------------------------
@mcp.tool()
def edit_expense(
    expense_id: int,
    amount: float = None,
    category: str = None,
    subcategory: str = None,
    description: str = None,
    date: str = None
) -> dict:

    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()

    if not existing:
        return {"error": "Expense ID not found."}

    # Validate category
    if category:
        ok, msg = validate_category(category, subcategory)
        if not ok:
            return {"error": msg}

    # Validate date
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD."}

    new_amount = amount if amount is not None else existing[1]
    new_category = category if category is not None else existing[2]
    new_subcategory = subcategory if subcategory is not None else existing[3]
    new_description = description if description is not None else existing[4]
    new_date = date if date is not None else existing[5]

    with get_connection() as conn:
        conn.execute("""
            UPDATE expenses
            SET amount = ?, category = ?, subcategory = ?, description = ?, date = ?
            WHERE id = ?
        """, (new_amount, new_category, new_subcategory, new_description, new_date, expense_id))
        conn.commit()

    return {"message": "Expense updated successfully."}

# ---------------------------------------------------------
# 4. DELETE EXPENSE
# ---------------------------------------------------------
@mcp.tool()
def delete_expense(expense_id: int) -> dict:
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()

    return {"message": "Expense deleted successfully."}

# ---------------------------------------------------------
# 5. SUMMARY
# ---------------------------------------------------------
@mcp.tool()
def summarize_expenses() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT amount, category FROM expenses").fetchall()

    total = sum(r[0] for r in rows)

    summary = {}
    for amount, category in rows:
        summary[category] = summary.get(category, 0) + amount

    return {
        "total_spent": total,
        "category_summary": summary,
        "total_entries": len(rows)
    }

# ---------------------------------------------------------
# 6. CATEGORY LIST
# ---------------------------------------------------------
@mcp.tool()
def list_categories() -> dict:
    return {"categories": CATEGORIES}

# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
