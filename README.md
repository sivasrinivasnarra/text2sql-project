# Text2SQL Application

A Text2SQL application that empowers non-technical users to query relational data using plain English.

## Features

- Natural language to SQL conversion
- Multi-table dataset support
- Metadata ingestion from CSV/DDL files
- Web interface for query input and result display
- File upload component for data registration
- SQL execution and tabular result display

## Architecture

### Backend (FastAPI)
- NL-to-SQL engine
- Metadata parsing and catalog management
- SQL execution engine
- File upload handling
- RESTful API endpoints

### Frontend (React + TypeScript)
- Query input interface
- File upload component
- SQL and result display
- Responsive design with Tailwind CSS

## Dataset

The application includes a sample HR schema with three interrelated tables:
- Employees
- Departments
- Projects

## Getting Started

### Backend
```bash
cd text2sql-backend
poetry install
poetry run fastapi dev app/main.py
```

### Frontend
```bash
cd text2sql-frontend
npm install
npm run dev
```

## API Endpoints

- `POST /upload-metadata` - Upload CSV/DDL metadata files
- `POST /query` - Convert natural language to SQL and execute
- `GET /tables` - Get available tables and schema information
- `GET /healthz` - Health check endpoint
