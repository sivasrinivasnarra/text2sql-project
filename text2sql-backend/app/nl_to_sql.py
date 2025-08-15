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
            
            if table_name.lower() == "customers":
                mappings.update({
                    "customer": table_name,
                    "client": table_name,
                    "account_holder": table_name,
                    "user": table_name,
                    "person": table_name,
                    "people": table_name
                })
            elif table_name.lower() == "accounts":
                mappings.update({
                    "account": table_name,
                    "bank_account": table_name,
                    "banking_account": table_name
                })
            elif table_name.lower() == "transactions":
                mappings.update({
                    "transaction": table_name,
                    "txn": table_name,
                    "payment": table_name,
                    "transfer": table_name,
                    "activity": table_name
                })
            elif table_name.lower() == "loans":
                mappings.update({
                    "loan": table_name,
                    "credit": table_name,
                    "lending": table_name,
                    "borrowing": table_name
                })
            elif table_name.lower() == "employees":
                mappings.update({
                    "employee": table_name,
                    "staff": table_name,
                    "worker": table_name,
                    "banker": table_name,
                    "teller": table_name
                })
            elif table_name.lower() == "branches":
                mappings.update({
                    "branch": table_name,
                    "office": table_name,
                    "location": table_name,
                    "bank_branch": table_name
                })
            elif table_name.lower() == "credit_cards":
                mappings.update({
                    "credit_card": table_name,
                    "card": table_name,
                    "credit": table_name
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
                
                if col_name.lower() in ["first_name", "last_name", "name"]:
                    mappings[table_name]["called"] = col_name
                    mappings[table_name]["named"] = col_name
                elif col_name.lower() == "balance":
                    mappings[table_name]["money"] = col_name
                    mappings[table_name]["funds"] = col_name
                    mappings[table_name]["amount"] = col_name
                elif col_name.lower() == "amount":
                    mappings[table_name]["value"] = col_name
                    mappings[table_name]["sum"] = col_name
                    mappings[table_name]["total"] = col_name
                elif col_name.lower() == "credit_limit":
                    mappings[table_name]["limit"] = col_name
                    mappings[table_name]["credit"] = col_name
                elif col_name.lower() == "interest_rate":
                    mappings[table_name]["rate"] = col_name
                    mappings[table_name]["interest"] = col_name
                elif col_name.lower() in ["open_date", "issue_date", "start_date"]:
                    mappings[table_name]["opened"] = col_name
                    mappings[table_name]["created"] = col_name
                    mappings[table_name]["started"] = col_name
                elif col_name.lower() in ["txn_date", "withdrawal_date", "payment_date"]:
                    mappings[table_name]["date"] = col_name
                    mappings[table_name]["when"] = col_name
                elif col_name.lower() == "role":
                    mappings[table_name]["job"] = col_name
                    mappings[table_name]["position"] = col_name
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
        if any(word in query for word in ["customer", "client", "people"]) and any(word in query for word in ["account", "savings", "checking"]):
            return "customers"
        
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
        
        if main_table == "customers":
            if any(word in query for word in ["account", "savings", "checking", "balance"]):
                from_clause += " c JOIN accounts a ON c.customer_id = a.customer_id"
                if any(word in query for word in ["savings", "checking", "business", "joint", "account_type", "type"]):
                    from_clause += " JOIN account_types at ON a.account_type_id = at.account_type_id"
        elif main_table == "accounts":
            if any(word in query for word in ["customer", "client", "name"]):
                from_clause += " a JOIN customers c ON a.customer_id = c.customer_id"
            if any(word in query for word in ["branch", "office", "location"]):
                from_clause += " a JOIN branches b ON a.branch_id = b.branch_id"
            if any(word in query for word in ["account_type", "type"]):
                from_clause += " a JOIN account_types at ON a.account_type_id = at.account_type_id"
        elif main_table == "transactions":
            if any(word in query for word in ["customer", "client", "account"]):
                from_clause += " t JOIN accounts a ON t.account_id = a.account_id JOIN customers c ON a.customer_id = c.customer_id"
        elif main_table == "loans":
            if any(word in query for word in ["customer", "client", "name"]):
                from_clause += " l JOIN customers c ON l.customer_id = c.customer_id"
            if any(word in query for word in ["loan_type", "type"]):
                from_clause += " l JOIN loan_types lt ON l.loan_type_id = lt.loan_type_id"
        elif main_table == "employees":
            if any(word in query for word in ["branch", "office", "location"]):
                from_clause += " e JOIN branches b ON e.branch_id = b.branch_id"
        
        return from_clause
    
    def _build_where_clause(self, query: str) -> Optional[str]:
        """Build WHERE clause from conditions in the query"""
        conditions = []
        
        amount_match = re.search(r'(over|above|more than|greater than)\s*\$?(\d+)k?', query)
        if amount_match:
            amount = int(amount_match.group(2))
            if 'k' in amount_match.group(0) or amount < 1000:
                amount *= 1000
            if "balance" in query or "account" in query:
                conditions.append(f"balance > {amount}")
            elif "amount" in query or "transaction" in query:
                conditions.append(f"amount > {amount}")
            elif "credit" in query or "limit" in query:
                conditions.append(f"credit_limit > {amount}")
        
        amount_match = re.search(r'(under|below|less than)\s*\$?(\d+)k?', query)
        if amount_match:
            amount = int(amount_match.group(2))
            if 'k' in amount_match.group(0) or amount < 1000:
                amount *= 1000
            if "balance" in query or "account" in query:
                conditions.append(f"balance < {amount}")
            elif "amount" in query or "transaction" in query:
                conditions.append(f"amount < {amount}")
            elif "credit" in query or "limit" in query:
                conditions.append(f"credit_limit < {amount}")
        
        date_match = re.search(r'(after|since)\s*(\d{4})', query)
        if date_match:
            year = date_match.group(2)
            if "open" in query or "account" in query:
                conditions.append(f"open_date > '{year}-01-01'")
            elif "transaction" in query:
                conditions.append(f"txn_date > '{year}-01-01'")
            elif "loan" in query:
                conditions.append(f"start_date > '{year}-01-01'")
        
        date_match = re.search(r'(before)\s*(\d{4})', query)
        if date_match:
            year = date_match.group(2)
            if "open" in query or "account" in query:
                conditions.append(f"open_date < '{year}-01-01'")
            elif "transaction" in query:
                conditions.append(f"txn_date < '{year}-01-01'")
            elif "loan" in query:
                conditions.append(f"start_date < '{year}-01-01'")
        
        account_type_match = re.search(r'(savings|checking|business|joint)', query)
        if account_type_match:
            account_type = account_type_match.group(1).capitalize()
            conditions.append(f"at.account_type = '{account_type}'")
        
        if "credit" in query and "transaction" in query:
            conditions.append("txn_type = 'credit'")
        elif "debit" in query and "transaction" in query:
            conditions.append("txn_type = 'debit'")
        
        return " AND ".join(conditions) if conditions else None
    
    def _build_order_clause(self, query: str, main_table: str) -> Optional[str]:
        """Build ORDER BY clause"""
        if "highest" in query:
            if "balance" in query:
                return "balance DESC"
            elif "amount" in query:
                return "amount DESC"
            elif "credit" in query:
                return "credit_limit DESC"
        elif "lowest" in query:
            if "balance" in query:
                return "balance ASC"
            elif "amount" in query:
                return "amount ASC"
            elif "credit" in query:
                return "credit_limit ASC"
        elif "newest" in query or "recent" in query:
            if main_table == "accounts":
                return "open_date DESC"
            elif main_table == "transactions":
                return "txn_date DESC"
            elif main_table == "loans":
                return "start_date DESC"
        elif "oldest" in query:
            if main_table == "accounts":
                return "open_date ASC"
            elif main_table == "transactions":
                return "txn_date ASC"
            elif main_table == "loans":
                return "start_date ASC"
        
        return None

nl_converter = NLToSQLConverter()
