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
        """Initialize database with sample data"""
        conn = self.get_connection()
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                manager_id INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                department_id INTEGER,
                salary INTEGER,
                hire_date DATE,
                position TEXT,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                department_id INTEGER,
                start_date DATE,
                end_date DATE,
                budget INTEGER,
                status TEXT,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        """)
        
        if conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0] == 0:
            self.load_sample_data()
        
        conn.commit()
    
    def load_sample_data(self):
        """Load sample data from CSV files"""
        conn = self.get_connection()
        sample_data_dir = Path(__file__).parent.parent / "sample_data"
        
        if (sample_data_dir / "departments.csv").exists():
            df = pd.read_csv(sample_data_dir / "departments.csv")
            df.to_sql("departments", conn, if_exists="replace", index=False)
        
        if (sample_data_dir / "employees.csv").exists():
            df = pd.read_csv(sample_data_dir / "employees.csv")
            df.to_sql("employees", conn, if_exists="replace", index=False)
        
        if (sample_data_dir / "projects.csv").exists():
            df = pd.read_csv(sample_data_dir / "projects.csv")
            df.to_sql("projects", conn, if_exists="replace", index=False)
        
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
