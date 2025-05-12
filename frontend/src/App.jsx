import { useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000/search'

function App() {
  const [form, setForm] = useState({
    tumor_type: '',
    test: '',
    gene_mutations: '',
    therapy: '',
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
      const res = await fetch(`${API_URL}?${params}`)
      const data = await res.json()
      if (data.error) {
        setError(data.error)
      } else {
        setResults(data.results || [])
        setColumns(data.columns || [])
      }
    } catch (err) {
      setError('Failed to fetch results.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>CDx: Companion Diagnostics & Precision Medicine Search</h1>
      </header>
      <section className="intro-section" style={{background: '#f5f7fa', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 2px 8px #e0e0e0'}}>
        <h2 style={{marginTop: 0}}>What are Companion Diagnostics and Precision Medicine?</h2>
        <p>
          <b>Companion diagnostics</b> are laboratory tests designed to identify patients who are most likely to benefit from a specific drug or therapy, or who may be at increased risk for serious side effects. These tests analyze genetic, protein, or other biomarkers to guide treatment decisions.
        </p>
        <p>
          <b>Precision medicine</b> is an innovative approach to tailoring disease prevention and treatment that takes into account individual variability in genes, environment, and lifestyle. By using companion diagnostics, healthcare providers can select the most effective, personalized therapies for each patient, improving outcomes and minimizing unnecessary treatments.
        </p>
      </section>
      <form className="search-form" onSubmit={handleSubmit}>
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
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      {error && <div className="error">{error}</div>}
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
