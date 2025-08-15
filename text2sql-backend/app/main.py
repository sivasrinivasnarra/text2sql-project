from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

from .database import db_manager
from .nl_to_sql import nl_converter

app = FastAPI(title="Text2SQL API", description="Convert natural language to SQL queries")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    sql: Optional[str]
    results: Optional[List[Dict[str, Any]]]
    explanation: str
    success: bool
    error: Optional[str] = None

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/tables")
async def get_tables():
    """Get database schema information"""
    try:
        schema = db_manager.get_schema_info()
        return {"schema": schema, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Convert natural language to SQL and execute the query"""
    try:
        conversion_result = nl_converter.convert_to_sql(request.query)
        
        if not conversion_result["success"]:
            return QueryResponse(
                sql=None,
                results=None,
                explanation=conversion_result["explanation"],
                success=False,
                error=conversion_result.get("error")
            )
        
        sql_query = conversion_result["sql"]
        
        results = db_manager.execute_query(sql_query)
        
        return QueryResponse(
            sql=sql_query,
            results=results,
            explanation=f"Successfully executed query: {conversion_result['explanation']}",
            success=True
        )
        
    except Exception as e:
        return QueryResponse(
            sql=None,
            results=None,
            explanation=f"Error processing query: {str(e)}",
            success=False,
            error=str(e)
        )

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), table_name: str = ""):
    """Upload CSV file and load data into database"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        if not table_name:
            table_name = Path(file.filename).stem
        
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        db_manager.load_csv_data(str(file_path), table_name)
        
        os.remove(file_path)
        
        return {
            "message": f"Successfully loaded data from {file.filename} into table {table_name}",
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sample-queries")
async def get_sample_queries():
    """Get sample natural language queries for testing"""
    return {
        "queries": [
            "Show me all employees",
            "List employees hired after 2018",
            "Find employees making over $80k",
            "Show all employees in engineering department",
            "List projects with their departments",
            "Find the highest paid employees",
            "Show employees hired in 2019",
            "List all departments and their managers"
        ],
        "success": True
    }
