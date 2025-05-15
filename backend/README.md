TheraFind Backend - FastAPI app in backend/main.py

## Data Source
The application now fetches data from GitHub. The data source can be configured by updating the `GITHUB_DATA_URL` in `main.py` to point to your GitHub repository.

### Setup GitHub Data Repository
1. Create a GitHub repository to host your CSV data file
2. Upload your Table_Data.csv file to this repository
3. Update the `GITHUB_DATA_URL` in `main.py` with your repository URL

### Local Development
For local development, the app will fall back to local data files in the following locations if GitHub is not available:
- `../data/Table_Data.csv`
- `data/Table_Data.csv`
- `[project_root]/data/Table_Data.csv`
