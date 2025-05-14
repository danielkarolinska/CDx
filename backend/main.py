from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import csv
import os
import sys

app = FastAPI()

# Allow frontend to access backend - more specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://cdx-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Check different possible locations for the data file
possible_data_paths = [
    os.path.join(os.path.dirname(__file__), '../data/Table_Data.csv'),
    os.path.join(os.path.dirname(__file__), 'data/Table_Data.csv'),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/Table_Data.csv')
]

# Find the first path that exists
DATA_PATH = None
for path in possible_data_paths:
    if os.path.exists(path):
        DATA_PATH = path
        break

@app.get("/")
async def root():
    paths_checked = "\n".join(possible_data_paths)
    data_exists = DATA_PATH is not None
    return {
        "message": "CDx Backend API is running", 
        "endpoints": ["/search"],
        "data_path_exists": data_exists,
        "data_path": DATA_PATH if data_exists else None,
        "paths_checked": paths_checked,
        "cwd": os.getcwd(),
        "dir_contents": str(os.listdir('.' if os.getcwd() else '/'))
    }

# Helper to load table data
def load_table():
    if not DATA_PATH:
        return {"error": f"Data file not found. Checked paths: {possible_data_paths}"}
    
    try:
        with open(DATA_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            table = list(reader)
            if table:
                # Normalize column names (strip BOM and whitespace)
                normalized_table = []
                for row in table:
                    new_row = {}
                    for k, v in row.items():
                        key = k.replace('\ufeff', '').strip()
                        new_row[key] = v
                    normalized_table.append(new_row)
                return normalized_table
            return table
    except FileNotFoundError:
        return {"error": f"Data file not found at {DATA_PATH}"}
    except Exception as e:
        return {"error": f"Error loading data: {str(e)}"}

@app.get("/search")
def search(
    tumor_type: Optional[str] = Query(None),
    test: Optional[str] = Query(None),
    gene_mutations: Optional[str] = Query(None),
    therapy: Optional[str] = Query(None),
):
    """
    Search the table by any combination of fields. Case-insensitive, partial match.
    Returns results as a list of dicts and a 'columns' list for easy table rendering.
    
    IMPORTANT: This function returns ALL matching results without any deduplication.
    Different therapies (e.g., ROZLYTREK and VITRAKVI) for the same gene mutation, test,
    and tumor type will all be included in the results as separate rows.
    """
    table = load_table()
    
    # Check if there's an error loading the table
    if isinstance(table, dict) and "error" in table:
        return table
        
    results = []
    for row in table:
        # Skip rows missing expected columns
        if not all(k in row for k in ['Tumor Type', 'Test', 'Gene mutations', 'Therapy']):
            continue
        try:
            if tumor_type and tumor_type.lower() not in row['Tumor Type'].lower():
                continue
            if test and test.lower() not in row['Test'].lower():
                continue
            if gene_mutations and gene_mutations.lower() not in row['Gene mutations'].lower():
                continue
            if therapy and therapy.lower() not in row['Therapy'].lower():
                continue
        except KeyError as e:
            return {"error": f"Missing expected column: {e}"}
        results.append(row)
    # Define columns for table rendering (in order)
    columns = ['Tumor Type', 'Test', 'Gene mutations', 'Therapy']
    return {
        "columns": columns, 
        "results": results,
        "total_matches": len(results)
    }
