import re
from typing import Dict, List, Any, Optional
from .database import db_manager

class NLToSQLConverter:
    def __init__(self):
        self.schema = db_manager.get_schema_info()
        self.table_mappings = self._build_table_mappings()
        self.column_mappings = self._build_column_mappings()
    
    def _build_table_mappings(self) -> Dict[str, str]:
        """Build mappings from common terms to table names"""
        mappings = {}
        for table_name in self.schema.keys():
            mappings[table_name.lower()] = table_name
            
            if table_name.lower() == "employees":
                mappings.update({
                    "employee": table_name,
                    "staff": table_name,
                    "worker": table_name,
                    "people": table_name,
                    "person": table_name
                })
            elif table_name.lower() == "departments":
                mappings.update({
                    "department": table_name,
                    "dept": table_name,
                    "division": table_name,
                    "team": table_name
                })
            elif table_name.lower() == "projects":
                mappings.update({
                    "project": table_name,
                    "initiative": table_name,
                    "task": table_name
                })
        
        return mappings
    
    def _build_column_mappings(self) -> Dict[str, Dict[str, str]]:
        """Build mappings from common terms to column names for each table"""
        mappings = {}
        
        for table_name, table_info in self.schema.items():
            mappings[table_name] = {}
            for column in table_info["columns"]:
                col_name = column["name"]
                mappings[table_name][col_name.lower()] = col_name
                
                if col_name.lower() in ["name", "title"]:
                    mappings[table_name]["called"] = col_name
                    mappings[table_name]["named"] = col_name
                elif col_name.lower() == "salary":
                    mappings[table_name]["pay"] = col_name
                    mappings[table_name]["wage"] = col_name
                    mappings[table_name]["income"] = col_name
                    mappings[table_name]["earning"] = col_name
                elif col_name.lower() == "hire_date":
                    mappings[table_name]["hired"] = col_name
                    mappings[table_name]["joined"] = col_name
                    mappings[table_name]["started"] = col_name
                elif col_name.lower() == "position":
                    mappings[table_name]["job"] = col_name
                    mappings[table_name]["role"] = col_name
                    mappings[table_name]["title"] = col_name
        
        return mappings
    
    def convert_to_sql(self, natural_query: str) -> Dict[str, Any]:
        """Convert natural language query to SQL"""
        try:
            query_lower = natural_query.lower().strip()
            
            if any(word in query_lower for word in ["show", "list", "get", "find", "display", "what", "who"]):
                sql_query = self._build_select_query(query_lower)
            else:
                raise ValueError("Query type not supported. Please use queries that ask to show, list, get, or find information.")
            
            return {
                "sql": sql_query,
                "explanation": f"Converted '{natural_query}' to SQL query",
                "success": True
            }
        
        except Exception as e:
            return {
                "sql": None,
                "explanation": f"Error converting query: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    def _build_select_query(self, query: str) -> str:
        """Build SELECT query from natural language"""
        main_table = self._identify_main_table(query)
        if not main_table:
            raise ValueError("Could not identify the main table from the query")
        
        select_clause = self._build_select_clause(query, main_table)
        
        from_clause = self._build_from_clause(query, main_table)
        
        where_clause = self._build_where_clause(query)
        
        order_clause = self._build_order_clause(query, main_table)
        
        sql_parts = [f"SELECT {select_clause}", f"FROM {from_clause}"]
        
        if where_clause:
            sql_parts.append(f"WHERE {where_clause}")
        
        if order_clause:
            sql_parts.append(f"ORDER BY {order_clause}")
        
        return " ".join(sql_parts)
    
    def _identify_main_table(self, query: str) -> Optional[str]:
        """Identify the main table from the query"""
        for term, table in self.table_mappings.items():
            if term in query:
                return table
        return None
    
    def _build_select_clause(self, query: str, main_table: str) -> str:
        """Build SELECT clause"""
        if "all" in query or not any(col in query for col in self.column_mappings[main_table].keys()):
            return "*"
        
        selected_columns = []
        for term, column in self.column_mappings[main_table].items():
            if term in query:
                selected_columns.append(f"{main_table}.{column}")
        
        return ", ".join(selected_columns) if selected_columns else "*"
    
    def _build_from_clause(self, query: str, main_table: str) -> str:
        """Build FROM clause with necessary JOINs"""
        from_clause = main_table
        
        if main_table == "employees":
            if any(word in query for word in ["department", "dept"]):
                from_clause += " e JOIN departments d ON e.department_id = d.id"
        elif main_table == "projects":
            if any(word in query for word in ["department", "dept"]):
                from_clause += " p JOIN departments d ON p.department_id = d.id"
        
        return from_clause
    
    def _build_where_clause(self, query: str) -> Optional[str]:
        """Build WHERE clause from conditions in the query"""
        conditions = []
        
        salary_match = re.search(r'(over|above|more than|greater than)\s*\$?(\d+)k?', query)
        if salary_match:
            amount = int(salary_match.group(2))
            if 'k' in salary_match.group(0) or amount < 1000:
                amount *= 1000
            conditions.append(f"salary > {amount}")
        
        salary_match = re.search(r'(under|below|less than)\s*\$?(\d+)k?', query)
        if salary_match:
            amount = int(salary_match.group(2))
            if 'k' in salary_match.group(0) or amount < 1000:
                amount *= 1000
            conditions.append(f"salary < {amount}")
        
        date_match = re.search(r'(after|since)\s*(\d{4})', query)
        if date_match:
            year = date_match.group(2)
            conditions.append(f"hire_date > '{year}-01-01'")
        
        date_match = re.search(r'(before)\s*(\d{4})', query)
        if date_match:
            year = date_match.group(2)
            conditions.append(f"hire_date < '{year}-01-01'")
        
        dept_match = re.search(r'in\s+(engineering|marketing|hr|human resources|finance)', query)
        if dept_match:
            dept_name = dept_match.group(1)
            if dept_name in ["hr", "human resources"]:
                dept_name = "Human Resources"
            else:
                dept_name = dept_name.capitalize()
            conditions.append(f"department_id = (SELECT id FROM departments WHERE name = '{dept_name}')")
        
        return " AND ".join(conditions) if conditions else None
    
    def _build_order_clause(self, query: str, main_table: str) -> Optional[str]:
        """Build ORDER BY clause"""
        if "highest" in query and "salary" in query:
            return "salary DESC"
        elif "lowest" in query and "salary" in query:
            return "salary ASC"
        elif "newest" in query or "recent" in query:
            return "hire_date DESC"
        elif "oldest" in query:
            return "hire_date ASC"
        
        return None

nl_converter = NLToSQLConverter()
