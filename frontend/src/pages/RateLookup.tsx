import React, { useState } from 'react';
import { searchRates } from '../services/api';
import type { RateRow } from '../types';

const RateLookup: React.FC = () => {
  const [library, setLibrary] = useState('BCM2');
  const [searchText, setSearchText] = useState('');
  const [results, setResults] = useState<RateRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    
    try {
      const response = await searchRates({
        rate_library: library,
        search_text: searchText,
      });
      setResults(response.results || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <h2>Rate Library Lookup</h2>
      
      <form onSubmit={handleSearch} className="card">
        <div className="form-group">
          <label>Rate Library</label>
          <select value={library} onChange={(e) => setLibrary(e.target.value)}>
            <option value="BCM2">BCM2 - Building Costs m²</option>
            <option value="ELEM">ELEM - Elemental Costs</option>
            <option value="CPR">CPR - CostPlan Rates</option>
            <option value="DET">DET - Detailed Rates</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>Search Text</label>
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="e.g., Office, Warehouse, Concrete..."
            required
          />
        </div>
        
        <button type="submit" className="button" disabled={loading}>
          {loading ? 'Searching...' : 'Search Rates'}
        </button>
      </form>
      
      {error && <div className="alert alert-error">{error}</div>}
      
      {results.length > 0 && (
        <div className="card">
          <h3>Results ({results.length})</h3>
          
          <table className="table">
            <thead>
              <tr>
                <th>Description</th>
                <th>Unit</th>
                <th>Rates</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {results.map((rate, idx) => (
                <tr key={idx}>
                  <td>{rate.description}</td>
                  <td>{rate.unit || 'N/A'}</td>
                  <td>
                    {Object.entries(rate.city_values).map(([city, values]) => (
                      <div key={city}>
                        <strong>{city}:</strong> $
                        {values.low !== undefined && values.low !== null ? values.low.toFixed(2) : 'N/A'}
                        {values.high !== undefined && values.high !== null && 
                          ` - $${values.high.toFixed(2)}`}
                      </div>
                    ))}
                  </td>
                  <td>
                    <div className="source-ref">
                      <div>File: {rate.source_file}</div>
                      <div>Sheet: {rate.source_sheet}</div>
                      <div>Row: {rate.source_row_index}</div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {!loading && results.length === 0 && searchText && (
        <div className="alert alert-info">
          No results found for "{searchText}" in {library}.
        </div>
      )}
    </div>
  );
};

export default RateLookup;
