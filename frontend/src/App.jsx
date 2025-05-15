import { useState } from 'react'
import './App.css'

// Use localhost instead of 127.0.0.1 for better compatibility
const API_URL = process.env.NODE_ENV === 'production' 
  ? 'https://therafind-api-backend.onrender.com/search'
  : 'http://localhost:8000/search'

function App() {
  const [form, setForm] = useState({
    tumor_type: '',
    test: '',
    gene_mutations: '',
    therapy: '',
    drug_company: '',
    fda_year: ''
  })
  const [results, setResults] = useState([])
  const [columns, setColumns] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResults([])
    setColumns([])
    try {
      const params = Object.entries(form)
        .filter(([_, v]) => v)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join('&')
      
      console.log(`Fetching from: ${API_URL}?${params}`)
      
      const res = await fetch(`${API_URL}?${params}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        mode: 'cors',
      })
      
      if (!res.ok) {
        throw new Error(`HTTP error! Status: ${res.status}`)
      }
      
      const data = await res.json()
      console.log('API response:', data)
      
      if (data.error) {
        setError(data.error)
      } else {
        setResults(data.results || [])
        setColumns(data.columns || [])
      }
    } catch (err) {
      console.error('Fetch error:', err)
      setError(`Failed to fetch results. ${err.message || ''}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Companion Diagnostics & Precision Medicine</h1>
      </header>
      <section className="intro-section">
        <h2>What are Companion Diagnostics and Precision Medicine?</h2>
        <p>
          <b>Companion diagnostics</b> are laboratory tests designed to identify patients who are most likely to benefit from a specific drug or therapy, or who may be at increased risk for serious side effects. These tests analyze genetic, protein, or other biomarkers to guide treatment decisions.
        </p>
        <p>
          <b>Precision medicine</b> is an innovative approach to tailoring disease prevention and treatment that takes into account individual variability in genes, environment, and lifestyle. By using companion diagnostics, healthcare providers can select the most effective, personalized therapies for each patient, improving outcomes and minimizing unnecessary treatments.
        </p>
      </section>
      <form className="search-form" onSubmit={handleSubmit}>
        <div className="search-instructions">
          <p>Welcome to TheraFind, your smart companion in precision medicine. Our platform empowers patients and healthcare providers to identify the most effective, personalized therapies using companion diagnostics.</p>
          <p>Please consult with your doctor for insurance coverage and treatment options.</p>
        </div>
        <div className="form-row">
          <input
            type="text"
            name="tumor_type"
            placeholder="Tumor Type"
            value={form.tumor_type}
            onChange={handleChange}
          />
          <input
            type="text"
            name="test"
            placeholder="Test"
            value={form.test}
            onChange={handleChange}
          />
        </div>
        <div className="form-row">
          <input
            type="text"
            name="gene_mutations"
            placeholder="Gene Mutations"
            value={form.gene_mutations}
            onChange={handleChange}
          />
          <input
            type="text"
            name="therapy"
            placeholder="Therapy"
            value={form.therapy}
            onChange={handleChange}
          />
        </div>
        <div className="form-row">
          <input
            type="text"
            name="drug_company"
            placeholder="Drug Company"
            value={form.drug_company}
            onChange={handleChange}
          />
          <input
            type="text"
            name="fda_year"
            placeholder="FDA Approval Year"
            value={form.fda_year}
            onChange={handleChange}
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      {error && <div className="error">{error}</div>}
      <div className="results-info">
        {results.length > 0 && (
          <p>Found {results.length} matching results</p>
        )}
      </div>
      <div className="results-table">
        {results.length > 0 ? (
          <table>
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.map((row, i) => (
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col}>{row[col]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          !loading && <div className="no-results">No results found.</div>
        )}
      </div>
    </div>
  )
}

export default App
