from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import pandas as pd
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import io
import csv

app = FastAPI(title="Text2SQL Banking Application", version="1.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

DATABASE_PATH = ":memory:"
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    sql: str
    results: List[Dict[str, Any]]
    success: bool
    error: Optional[str] = None

class TableInfo(BaseModel):
    name: str
    columns: List[Dict[str, str]]
    sample_data: List[Dict[str, Any]]

def init_banking_database():
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            date_joined DATE NOT NULL,
            customer_status TEXT DEFAULT 'active'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            account_type TEXT NOT NULL,
            balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
            interest_rate DECIMAL(5,4) DEFAULT 0.0000,
            date_opened DATE NOT NULL,
            account_status TEXT DEFAULT 'active',
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY,
            account_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount DECIMAL(15,2) NOT NULL,
            description TEXT,
            transaction_date DATETIME NOT NULL,
            balance_after DECIMAL(15,2) NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts (account_id)
        )
    """)
    
    sample_customers = [
        (1, 'John', 'Smith', 'john.smith@email.com', '555-0101', '123 Main St', 'New York', 'NY', '10001', '2020-01-15', 'active'),
        (2, 'Sarah', 'Johnson', 'sarah.johnson@email.com', '555-0102', '456 Oak Ave', 'Los Angeles', 'CA', '90210', '2019-03-22', 'active'),
        (3, 'Michael', 'Brown', 'michael.brown@email.com', '555-0103', '789 Pine Rd', 'Chicago', 'IL', '60601', '2021-07-10', 'active'),
        (4, 'Emily', 'Davis', 'emily.davis@email.com', '555-0104', '321 Elm St', 'Houston', 'TX', '77001', '2018-11-05', 'active'),
        (5, 'David', 'Wilson', 'david.wilson@email.com', '555-0105', '654 Maple Dr', 'Phoenix', 'AZ', '85001', '2022-02-28', 'active')
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO customers 
        (customer_id, first_name, last_name, email, phone, address, city, state, zip_code, date_joined, customer_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_customers)
    
    sample_accounts = [
        (1, 1, 'CHK-001-2020', 'checking', 2500.00, 0.0100, '2020-01-15', 'active'),
        (2, 1, 'SAV-001-2020', 'savings', 15000.00, 0.0250, '2020-01-15', 'active'),
        (3, 2, 'CHK-002-2019', 'checking', 3200.50, 0.0100, '2019-03-22', 'active'),
        (4, 2, 'SAV-002-2019', 'savings', 25000.00, 0.0250, '2019-03-22', 'active'),
        (5, 3, 'CHK-003-2021', 'checking', 1800.75, 0.0100, '2021-07-10', 'active'),
        (6, 4, 'CHK-004-2018', 'checking', 4500.25, 0.0100, '2018-11-05', 'active'),
        (7, 4, 'SAV-004-2018', 'savings', 50000.00, 0.0300, '2018-11-05', 'active'),
        (8, 5, 'CHK-005-2022', 'checking', 750.00, 0.0100, '2022-02-28', 'active')
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO accounts 
        (account_id, customer_id, account_number, account_type, balance, interest_rate, date_opened, account_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_accounts)
    
    sample_transactions = [
        (1, 1, 'deposit', 1000.00, 'Initial deposit', '2020-01-15 10:00:00', 1000.00),
        (2, 1, 'deposit', 1500.00, 'Payroll deposit', '2020-01-30 09:00:00', 2500.00),
        (3, 1, 'withdrawal', -200.00, 'ATM withdrawal', '2020-02-05 14:30:00', 2300.00),
        (4, 1, 'deposit', 200.00, 'Cash deposit', '2020-02-10 11:15:00', 2500.00),
        (5, 2, 'deposit', 15000.00, 'Initial savings deposit', '2020-01-15 10:30:00', 15000.00),
        (6, 3, 'deposit', 2000.00, 'Initial deposit', '2019-03-22 09:30:00', 2000.00),
        (7, 3, 'deposit', 1200.50, 'Payroll deposit', '2019-04-01 08:00:00', 3200.50),
        (8, 4, 'deposit', 25000.00, 'Initial savings deposit', '2019-03-22 10:00:00', 25000.00),
        (9, 5, 'deposit', 2000.00, 'Initial deposit', '2021-07-10 15:00:00', 2000.00),
        (10, 5, 'withdrawal', -201.25, 'Debit card purchase', '2021-07-15 12:30:00', 1798.75),
        (11, 6, 'deposit', 5000.00, 'Initial deposit', '2018-11-05 11:00:00', 5000.00),
        (12, 6, 'withdrawal', -499.75, 'Check payment', '2018-11-20 16:45:00', 4500.25),
        (13, 7, 'deposit', 50000.00, 'Initial savings deposit', '2018-11-05 11:30:00', 50000.00),
        (14, 8, 'deposit', 1000.00, 'Initial deposit', '2022-02-28 13:00:00', 1000.00),
        (15, 8, 'withdrawal', -250.00, 'ATM withdrawal', '2022-03-05 10:15:00', 750.00)
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO transactions 
        (transaction_id, account_id, transaction_type, amount, description, transaction_date, balance_after)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_transactions)
    
    conn.commit()

class NLToSQLConverter:
    def __init__(self):
        self.table_schemas = {
            'customers': {
                'columns': ['customer_id', 'first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'zip_code', 'date_joined', 'customer_status'],
                'description': 'Customer information including personal details and contact information'
            },
            'accounts': {
                'columns': ['account_id', 'customer_id', 'account_number', 'account_type', 'balance', 'interest_rate', 'date_opened', 'account_status'],
                'description': 'Bank accounts owned by customers including checking and savings accounts'
            },
            'transactions': {
                'columns': ['transaction_id', 'account_id', 'transaction_type', 'amount', 'description', 'transaction_date', 'balance_after'],
                'description': 'Financial transactions including deposits, withdrawals, and transfers'
            }
        }
        
        self.query_patterns = [
            (r'(?:show|list|find|get).*customers?.*(?:from|in)\s+(\w+)', 'SELECT * FROM customers WHERE city = "{}" OR state = "{}"'),
            (r'(?:show|list|find|get).*customers?.*(?:joined|registered).*after\s+(\d{4})', 'SELECT * FROM customers WHERE date_joined > "{}-01-01"'),
            (r'(?:show|list|find|get).*customers?.*(?:joined|registered).*before\s+(\d{4})', 'SELECT * FROM customers WHERE date_joined < "{}-01-01"'),
            (r'(?:show|list|find|get).*(?:all\s+)?customers?', 'SELECT * FROM customers'),
            
            (r'(?:show|list|find|get).*accounts?.*(?:with\s+)?balance.*(?:over|above|greater than)\s+\$?(\d+)', 'SELECT * FROM accounts WHERE balance > {}'),
            (r'(?:show|list|find|get).*accounts?.*(?:with\s+)?balance.*(?:under|below|less than)\s+\$?(\d+)', 'SELECT * FROM accounts WHERE balance < {}'),
            (r'(?:show|list|find|get).*savings?\s+accounts?', 'SELECT * FROM accounts WHERE account_type = "savings"'),
            (r'(?:show|list|find|get).*checking\s+accounts?', 'SELECT * FROM accounts WHERE account_type = "checking"'),
            (r'(?:show|list|find|get).*accounts?.*opened.*after\s+(\d{4})', 'SELECT * FROM accounts WHERE date_opened > "{}-01-01"'),
            (r'(?:show|list|find|get).*accounts?.*opened.*before\s+(\d{4})', 'SELECT * FROM accounts WHERE date_opened < "{}-01-01"'),
            (r'(?:show|list|find|get).*(?:all\s+)?accounts?', 'SELECT * FROM accounts'),
            
            (r'(?:show|list|find|get).*transactions?.*(?:over|above|greater than)\s+\$?(\d+)', 'SELECT * FROM transactions WHERE ABS(amount) > {}'),
            (r'(?:show|list|find|get).*transactions?.*(?:under|below|less than)\s+\$?(\d+)', 'SELECT * FROM transactions WHERE ABS(amount) < {}'),
            (r'(?:show|list|find|get).*deposits?', 'SELECT * FROM transactions WHERE transaction_type = "deposit"'),
            (r'(?:show|list|find|get).*withdrawals?', 'SELECT * FROM transactions WHERE transaction_type = "withdrawal"'),
            (r'(?:show|list|find|get).*transactions?.*after\s+(\d{4})', 'SELECT * FROM transactions WHERE transaction_date > "{}-01-01"'),
            (r'(?:show|list|find|get).*transactions?.*before\s+(\d{4})', 'SELECT * FROM transactions WHERE transaction_date < "{}-01-01"'),
            (r'(?:show|list|find|get).*(?:all\s+)?transactions?', 'SELECT * FROM transactions'),
            
            (r'(?:show|list|find|get).*customers?.*(?:with\s+)?accounts?', 'SELECT c.*, a.* FROM customers c JOIN accounts a ON c.customer_id = a.customer_id'),
            (r'(?:show|list|find|get).*accounts?.*(?:with\s+)?transactions?', 'SELECT a.*, t.* FROM accounts a JOIN transactions t ON a.account_id = t.account_id'),
            (r'(?:show|list|find|get).*customers?.*(?:with\s+)?transactions?', 'SELECT c.*, t.* FROM customers c JOIN accounts a ON c.customer_id = a.customer_id JOIN transactions t ON a.account_id = t.account_id'),
            
            (r'(?:total|sum).*balance', 'SELECT SUM(balance) as total_balance FROM accounts'),
            (r'(?:average|avg).*balance', 'SELECT AVG(balance) as average_balance FROM accounts'),
            (r'(?:count|number of).*customers?', 'SELECT COUNT(*) as customer_count FROM customers'),
            (r'(?:count|number of).*accounts?', 'SELECT COUNT(*) as account_count FROM accounts'),
            (r'(?:count|number of).*transactions?', 'SELECT COUNT(*) as transaction_count FROM transactions'),
        ]
    
    def convert_to_sql(self, natural_query: str) -> str:
        query_lower = natural_query.lower().strip()
        
        for pattern, sql_template in self.query_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if '{}' in sql_template:
                    return sql_template.format(*match.groups())
                elif '"{}"' in sql_template:
                    return sql_template.format(*match.groups())
                else:
                    return sql_template
        
        return "SELECT 'Query not recognized. Please try a different phrasing.' as message"

init_banking_database()
nl_converter = NLToSQLConverter()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/tables", response_model=List[TableInfo])
async def get_tables():
    """Get information about all tables in the database"""
    cursor = conn.cursor()
    tables = []
    
    for table_name in ['customers', 'accounts', 'transactions']:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        sample_data = [dict(row) for row in cursor.fetchall()]
        
        tables.append(TableInfo(
            name=table_name,
            columns=columns,
            sample_data=sample_data
        ))
    
    return tables

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Convert natural language to SQL and execute the query"""
    try:
        sql_query = nl_converter.convert_to_sql(request.query)
        
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = [dict(row) for row in cursor.fetchall()]
        
        return QueryResponse(
            sql=sql_query,
            results=results,
            success=True
        )
    
    except Exception as e:
        return QueryResponse(
            sql=sql_query if 'sql_query' in locals() else "",
            results=[],
            success=False,
            error=str(e)
        )

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and process CSV file to create new table"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        table_name = file.filename.replace('.csv', '').lower().replace(' ', '_')
        
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        return {"message": f"Successfully uploaded {file.filename} as table '{table_name}'", "table_name": table_name}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sample-queries")
async def get_sample_queries():
    """Get sample banking queries for the frontend"""
    return {
        "queries": [
            "Show all customers",
            "List customers from New York",
            "Find accounts with balance over $10000",
            "Show all savings accounts",
            "List transactions over $1000",
            "Show customers with accounts",
            "Find deposits made after 2020",
            "What is the total balance across all accounts?",
            "Count the number of customers",
            "Show all withdrawals"
        ]
    }
