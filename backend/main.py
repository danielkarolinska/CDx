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

@app.get("/search")
def search(
    tumor_type: Optional[str] = Query(None),
    test: Optional[str] = Query(None),
    gene_mutations: Optional[str] = Query(None),
    therapy: Optional[str] = Query(None),
    drug_company: Optional[str] = Query(None),
    fda_year: Optional[str] = Query(None),
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
    has_search_terms = any([tumor_type, test, gene_mutations, therapy, drug_company, fda_year])
    if not has_search_terms:
        results = table
    else:
        # Go through each row
        for row in table:
            # Skip rows missing expected columns
            if not all(key in row for key in ['Tumor Type', 'Test', 'Gene mutations', 'Therapy']):
                continue
                
            # Check each term against its corresponding column
            tumor_match = matches(row.get('Tumor Type', ''), tumor_type)
            test_match = matches(row.get('Test', ''), test)
            gene_match = matches(row.get('Gene mutations', ''), gene_mutations)
            therapy_match = matches(row.get('Therapy', ''), therapy)
            
            # Check the optional columns if they exist
            drug_company_match = True
            if drug_company and 'Drug Company' in row:
                drug_company_match = matches(row['Drug Company'], drug_company)
                
            fda_year_match = True
            if fda_year and 'FDA Approved Year' in row:
                fda_year_match = matches(row['FDA Approved Year'], fda_year)
            
            # Row matches if ALL provided search terms match in their respective columns
            if tumor_match and test_match and gene_match and therapy_match and drug_company_match and fda_year_match:
                results.append(row)
    
    # Define columns for table rendering (in order) - including new columns
    columns = ['Tumor Type', 'Test', 'Gene mutations', 'Therapy']
    
    # Check if the new columns exist in the results
    if results and 'Drug Company' in results[0]:
        columns.append('Drug Company')
    if results and 'FDA Approved Year' in results[0]:
        columns.append('FDA Approved Year')
    
    # Return results with diagnostic info
    search_info = {
        "search_terms": {
            "tumor_type": tumor_type,
            "test": test, 
            "gene_mutations": gene_mutations,
            "therapy": therapy,
            "drug_company": drug_company,
            "fda_year": fda_year
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
