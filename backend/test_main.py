from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "CDx Backend API is running", "endpoints": ["/search"]}

def test_search_no_params():
    response = client.get("/search")
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "results" in data
    assert data["columns"] == ['Tumor Type', 'Test', 'Gene mutations', 'Therapy']

def test_search_with_tumor_type():
    response = client.get("/search?tumor_type=Lung")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    # All results should contain "lung" (case-insensitive) in their tumor type
    for result in data["results"]:
        assert "lung" in result["Tumor Type"].lower()

def test_search_with_multiple_params():
    response = client.get("/search?tumor_type=Lung&test=PCR")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    # All results should contain both "lung" in tumor type and "PCR" in test (case-insensitive)
    for result in data["results"]:
        assert "lung" in result["Tumor Type"].lower()
        assert "pcr" in result["Test"].lower()

def test_search_case_insensitive():
    response = client.get("/search?tumor_type=lung")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    # Should find results despite lowercase query
    for result in data["results"]:
        assert "lung" in result["Tumor Type"].lower() 