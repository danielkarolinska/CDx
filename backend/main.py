from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import csv
import os
import sys
import re

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

def text_contains(haystack, needle):
    """
    Enhanced search function that handles special cases for gene mutations
    and ensures partial matching works correctly.
    """
    if not needle or not haystack:
        return True
    
    # Convert both to lowercase for case-insensitive comparison
    haystack_lower = haystack.lower()
    needle_lower = needle.lower()
    
    # Direct substring check
    if needle_lower in haystack_lower:
        return True
    
    # Special handling for gene mutations like NTRK vs NTRK1/2/3
    # Check if needle is a gene name prefix in gene mutation strings
    if re.search(r'\b' + re.escape(needle_lower) + r'[0-9/]*\b', haystack_lower):
        return True
    
    return False

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
            # Use the enhanced text_contains function for better matching
            if tumor_type and not text_contains(row['Tumor Type'], tumor_type):
                continue
            if test and not text_contains(row['Test'], test):
                continue
            if gene_mutations and not text_contains(row['Gene mutations'], gene_mutations):
                continue
            if therapy and not text_contains(row['Therapy'], therapy):
                continue
            results.append(row)
        except KeyError as e:
            return {"error": f"Missing expected column: {e}"}
    
    # Define columns for table rendering (in order)
    columns = ['Tumor Type', 'Test', 'Gene mutations', 'Therapy']
    
    # Diagnostic information for specific searches
    diagnostic_info = {}
    if gene_mutations in ["NTRK", "ALK"]:
        diagnostic_info["search_term"] = gene_mutations
        diagnostic_info["matching_rows"] = len(results)
        diagnostic_info["expected_minimum"] = 3 if gene_mutations == "NTRK" else 5
    
    return {
        "columns": columns, 
        "results": results,
        "total_matches": len(results),
        "diagnostic_info": diagnostic_info if diagnostic_info else None
    }
