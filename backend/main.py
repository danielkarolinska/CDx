from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import csv
import os
import sys
import re
import requests
import io

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
        "https://therafind-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# GitHub raw content URL for the data file
GITHUB_DATA_URL = "https://raw.githubusercontent.com/danielkarolinska/CDx/main/data/Table_Data.csv"

# Check different possible locations for the data file (fallback)
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
        "message": "TheraFind Backend API is running", 
        "endpoints": ["/search"],
        "data_source": "GitHub",
        "github_url": GITHUB_DATA_URL,
        "data_path_exists": data_exists,
        "data_path": DATA_PATH if data_exists else None,
        "paths_checked": paths_checked,
        "cwd": os.getcwd(),
        "dir_contents": str(os.listdir('.' if os.getcwd() else '/'))
    }

# Helper to load table data from GitHub
def load_table():
    try:
        # First try to fetch from GitHub
        response = requests.get(GITHUB_DATA_URL)
        if response.status_code == 200:
            # Parse the CSV from the response content
            csv_content = io.StringIO(response.text)
            reader = csv.DictReader(csv_content)
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
        else:
            # Fallback to local file if GitHub fetch fails
            return load_local_table()
    except Exception as e:
        # Fallback to local file if GitHub fetch fails
        print(f"Error fetching from GitHub: {str(e)}")
        return load_local_table()

# Helper to load table data from local file as fallback
def load_local_table():
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
    diagnostic_name: Optional[str] = Query(None),
    indication_sample: Optional[str] = Query(None),
    drug_trade_name: Optional[str] = Query(None),
    biomarker: Optional[str] = Query(None),
    biomarker_details: Optional[str] = Query(None),
    approval_date: Optional[str] = Query(None),
):
    """
    Search the table by any combination of fields. Case-insensitive, partial match.
    Rule: If a search term matches in its corresponding column, the whole row will be returned.
    All matching rows are returned without deduplication.
    """
    table = load_table()
    
    # Check if there's an error loading the table
    if isinstance(table, dict) and "error" in table:
        return table
        
    results = []
    
    # Simple function to check if a field matches the search term
    def matches(field_value, search_term):
        if not search_term:
            return True  # Empty search terms match everything in their column
        if not field_value:
            return False
        # Simple case insensitive check
        return search_term.lower() in field_value.lower()
    
    # If no search terms provided, return all rows
    has_search_terms = any([diagnostic_name, indication_sample, drug_trade_name, biomarker, biomarker_details, approval_date])
    if not has_search_terms:
        results = table
    else:
        # Go through each row
        for row in table:
            # Check if all required columns exist
            diag_name_col = 'Diagnostic Name (Manufacturer)'
            indication_col = 'Indication - Sample Type'
            drug_name_col = 'Drug Trade Name (Generic) NDA / BLA'
            biomarker_col = 'Biomarker(s)'
            biomarker_details_col = 'Biomarker(s) (Details)'
            approval_date_col = 'Approval/Clearance/Grant Date'
            
            # Skip rows missing expected columns
            if not all(key in row for key in [diag_name_col, indication_col, drug_name_col, biomarker_col, biomarker_details_col, approval_date_col]):
                continue
                
            # Check each term against its corresponding column
            diag_match = matches(row.get(diag_name_col, ''), diagnostic_name)
            indication_match = matches(row.get(indication_col, ''), indication_sample)
            drug_match = matches(row.get(drug_name_col, ''), drug_trade_name)
            biomarker_match = matches(row.get(biomarker_col, ''), biomarker)
            biomarker_details_match = matches(row.get(biomarker_details_col, ''), biomarker_details)
            approval_date_match = matches(row.get(approval_date_col, ''), approval_date)
            
            # Row matches if ALL provided search terms match in their respective columns
            if diag_match and indication_match and drug_match and biomarker_match and biomarker_details_match and approval_date_match:
                results.append(row)
    
    # Define columns for table rendering (in order)
    columns = [
        'Diagnostic Name (Manufacturer)',
        'Indication - Sample Type',
        'Drug Trade Name (Generic) NDA / BLA',
        'Biomarker(s)',
        'Biomarker(s) (Details)',
        'Approval/Clearance/Grant Date'
    ]
    
    # Return results with diagnostic info
    search_info = {
        "search_terms": {
            "diagnostic_name": diagnostic_name,
            "indication_sample": indication_sample, 
            "drug_trade_name": drug_trade_name,
            "biomarker": biomarker,
            "biomarker_details": biomarker_details,
            "approval_date": approval_date
        },
        "matched_rows": len(results),
        "total_rows": len(table) if isinstance(table, list) else 0,
        "search_rule": "Match search terms in their corresponding columns"
    }
    
    return {
        "columns": columns, 
        "results": results,
        "total_matches": len(results),
        "search_info": search_info
    }
