from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import csv
import os

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

DATA_PATH = os.path.join(os.path.dirname(__file__), '../data/Table_Data.csv')

@app.get("/")
async def root():
    return {"message": "CDx Backend API is running", "endpoints": ["/search"]}

# Helper to load table data
def load_table():
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
    return {"columns": columns, "results": results}
