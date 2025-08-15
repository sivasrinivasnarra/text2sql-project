import sqlite3
import pandas as pd
import os
from typing import List, Dict, Any
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str = "text2sql.db"):
        self.db_path = db_path
        self.connection = None
        self.setup_database()
    
    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def setup_database(self):
        """Initialize database with banking sample data"""
        conn = self.get_connection()
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS account_types (
                account_type_id INTEGER PRIMARY KEY,
                account_type TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS loan_types (
                loan_type_id INTEGER PRIMARY KEY,
                loan_type TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS branches (
                branch_id INTEGER PRIMARY KEY,
                branch_name TEXT NOT NULL,
                city TEXT,
                state TEXT,
                manager_name TEXT,
                open_date DATE
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                dob DATE,
                region TEXT,
                address TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                role TEXT,
                branch_id INTEGER,
                FOREIGN KEY (branch_id) REFERENCES branches (branch_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                branch_id INTEGER,
                account_type_id INTEGER,
                balance REAL,
                open_date DATE,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
                FOREIGN KEY (branch_id) REFERENCES branches (branch_id),
                FOREIGN KEY (account_type_id) REFERENCES account_types (account_type_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credit_cards (
                card_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                account_id INTEGER,
                card_type TEXT,
                credit_limit REAL,
                issue_date DATE,
                processed_by_employee_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
                FOREIGN KEY (account_id) REFERENCES accounts (account_id),
                FOREIGN KEY (processed_by_employee_id) REFERENCES employees (employee_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                account_id INTEGER,
                loan_type_id INTEGER,
                amount REAL,
                start_date DATE,
                term_months INTEGER,
                interest_rate REAL,
                issued_by_employee_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
                FOREIGN KEY (account_id) REFERENCES accounts (account_id),
                FOREIGN KEY (loan_type_id) REFERENCES loan_types (loan_type_id),
                FOREIGN KEY (issued_by_employee_id) REFERENCES employees (employee_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                txn_id INTEGER PRIMARY KEY,
                account_id INTEGER,
                txn_date DATE,
                amount REAL,
                txn_type TEXT,
                description TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (account_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS atm_withdrawals (
                withdrawal_id INTEGER PRIMARY KEY,
                account_id INTEGER,
                withdrawal_date DATE,
                amount REAL,
                atm_location TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (account_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS card_transactions (
                card_txn_id INTEGER PRIMARY KEY,
                card_id INTEGER,
                txn_date DATE,
                merchant TEXT,
                amount REAL,
                category TEXT,
                FOREIGN KEY (card_id) REFERENCES credit_cards (card_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS loan_payments (
                payment_id INTEGER PRIMARY KEY,
                loan_id INTEGER,
                payment_date DATE,
                amount REAL,
                payment_type TEXT,
                FOREIGN KEY (loan_id) REFERENCES loans (loan_id)
            )
        """)
        
        if conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
            self.load_sample_data()
        
        conn.commit()
    
    def load_sample_data(self):
        """Load banking sample data from CSV files"""
        conn = self.get_connection()
        sample_data_dir = Path(__file__).parent.parent / "sample_data"
        
        banking_tables = [
            "account_types", "loan_types", "branches", "customers", 
            "employees", "accounts", "credit_cards", "loans", 
            "transactions", "atm_withdrawals", "card_transactions", "loan_payments"
        ]
        
        for table_name in banking_tables:
            csv_file = sample_data_dir / f"{table_name}.csv"
            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file)
                    df.to_sql(table_name, conn, if_exists="replace", index=False)
                    print(f"Loaded {len(df)} records into {table_name}")
                except Exception as e:
                    print(f"Error loading {table_name}: {str(e)}")
        
        conn.commit()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(query)
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        conn = self.get_connection()
        schema = {}
        
        tables = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        
        for table in tables:
            table_name = table[0]
            columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            schema[table_name] = {
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "nullable": not col[3],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]
            }
            
            foreign_keys = conn.execute(f"PRAGMA foreign_key_list({table_name})").fetchall()
            if foreign_keys:
                schema[table_name]["foreign_keys"] = [
                    {
                        "column": fk[3],
                        "references_table": fk[2],
                        "references_column": fk[4]
                    }
                    for fk in foreign_keys
                ]
        
        return schema
    
    def load_csv_data(self, file_path: str, table_name: str):
        """Load data from CSV file into specified table"""
        conn = self.get_connection()
        df = pd.read_csv(file_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()

db_manager = DatabaseManager()
