import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import { config } from './config';

// Mock fetch
global.fetch = jest.fn();

describe('App Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders the header and search form', () => {
    render(<App />);
    
    // Check if header is present
    expect(screen.getByText(config.appTitle)).toBeInTheDocument();
    expect(screen.getByText(`v${config.version}`)).toBeInTheDocument();
    
    // Check if all search inputs are present
    expect(screen.getByPlaceholderText('Tumor Type')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Test')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Gene Mutations')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Therapy')).toBeInTheDocument();
    
    // Check if search button is present
    expect(screen.getByText('Search')).toBeInTheDocument();
  });

  it('performs search when form is submitted', async () => {
    const mockResponse = {
      columns: ['Tumor Type', 'Test', 'Gene mutations', 'Therapy'],
      results: [
        {
          'Tumor Type': 'Non-small cell lung cancer (NSCLC)',
          'Test': 'PCR',
          'Gene mutations': 'EGFR',
          'Therapy': 'Erlotinib'
        }
      ]
    };

    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })
    );

    render(<App />);

    // Fill in search form
    fireEvent.change(screen.getByPlaceholderText('Tumor Type'), {
      target: { value: 'lung' }
    });

    // Submit form
    fireEvent.click(screen.getByText('Search'));

    // Wait for results to be displayed
    await waitFor(() => {
      expect(screen.getByText('Non-small cell lung cancer (NSCLC)')).toBeInTheDocument();
      expect(screen.getByText('PCR')).toBeInTheDocument();
      expect(screen.getByText('EGFR')).toBeInTheDocument();
      expect(screen.getByText('Erlotinib')).toBeInTheDocument();
    });

    // Verify fetch was called with correct URL
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/search?tumor_type=lung')
    );
  });

  it('displays error message when API call fails', async () => {
    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 500
      })
    );

    render(<App />);

    // Submit form
    fireEvent.click(screen.getByText('Search'));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('HTTP error! status: 500')).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching results', async () => {
    fetch.mockImplementationOnce(() =>
      new Promise(resolve =>
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ results: [] })
        }), 100)
      )
    );

    render(<App />);

    // Submit form
    fireEvent.click(screen.getByText('Search'));

    // Check for loading state
    expect(screen.getByText('Searching...')).toBeInTheDocument();

    // Wait for loading state to finish
    await waitFor(() => {
      expect(screen.queryByText('Searching...')).not.toBeInTheDocument();
    });
  });

  it('displays error message when API returns an error', async () => {
    const errorMessage = 'Missing expected column: Gene mutations';
    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ error: errorMessage })
      })
    );

    render(<App />);

    // Submit form
    fireEvent.click(screen.getByText('Search'));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Verify no results are shown
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('handles empty search results correctly', async () => {
    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          columns: ['Tumor Type', 'Test', 'Gene mutations', 'Therapy'],
          results: []
        })
      })
    );

    render(<App />);

    // Fill in search form with a query that will return no results
    fireEvent.change(screen.getByPlaceholderText('Tumor Type'), {
      target: { value: 'nonexistent' }
    });

    // Submit form
    fireEvent.click(screen.getByText('Search'));

    // Wait for no results message
    await waitFor(() => {
      expect(screen.getByText('No results found.')).toBeInTheDocument();
    });

    // Verify table is not shown
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
}); 