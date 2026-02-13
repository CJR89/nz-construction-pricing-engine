import React, { useState } from 'react';
import { calculateConceptEstimate } from '../services/api';
import type { ConceptEstimate } from '../types';

const ConceptEstimate: React.FC = () => {
  const [projectId, setProjectId] = useState('');
  const [estimate, setEstimate] = useState<ConceptEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    
    try {
      const result = await calculateConceptEstimate(projectId);
      setEstimate(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
      setEstimate(null);
    } finally {
      setLoading(false);
    }
  };
  
  const formatCurrency = (value?: number | null) => {
    if (value === undefined || value === null) return 'Not priced';
    return `$${value.toLocaleString('en-NZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };
  
  return (
    <div>
      <h2>Concept Estimate</h2>
      
      <form onSubmit={handleCalculate} className="card">
        <div className="form-group">
          <label>Project ID</label>
          <input
            type="text"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            placeholder="e.g., PROJ-001"
            required
          />
        </div>
        
        <button type="submit" className="button" disabled={loading}>
          {loading ? 'Calculating...' : 'Calculate Estimate'}
        </button>
      </form>
      
      {error && <div className="alert alert-error">{error}</div>}
      
      {estimate && (
        <>
          {estimate.disclaimer.startsWith('BLOCKED') ? (
            <div className="alert alert-error">
              <strong>{estimate.disclaimer}</strong>
            </div>
          ) : (
            <>
              <div className="card">
                <h3>Estimate Summary</h3>
                
                <table className="table">
                  <tbody>
                    <tr>
                      <th>Base Build Cost</th>
                      <td>{formatCurrency(estimate.base_build_cost)}</td>
                    </tr>
                    {estimate.fitout_cost !== undefined && estimate.fitout_cost !== null && (
                      <tr>
                        <th>Fitout Cost</th>
                        <td>{formatCurrency(estimate.fitout_cost)}</td>
                      </tr>
                    )}
                    <tr style={{ fontWeight: 'bold', borderTop: '2px solid #333' }}>
                      <th>Subtotal</th>
                      <td>{formatCurrency(estimate.subtotal)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <div className="card">
                <h3>Line Items</h3>
                
                <table className="table">
                  <thead>
                    <tr>
                      <th>Description</th>
                      <th>Quantity</th>
                      <th>Unit</th>
                      <th>Rate</th>
                      <th>Amount</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {estimate.line_items.map((item, idx) => (
                      <tr key={idx}>
                        <td>
                          {item.description}
                          {item.note && <div style={{ fontSize: '12px', color: '#666' }}>{item.note}</div>}
                        </td>
                        <td>{item.quantity !== undefined && item.quantity !== null ? item.quantity.toFixed(2) : ''}</td>
                        <td>{item.unit || ''}</td>
                        <td>{item.rate !== undefined && item.rate !== null ? `$${item.rate.toFixed(2)}` : ''}</td>
                        <td>{formatCurrency(item.amount)}</td>
                        <td>
                          {item.source_file && (
                            <div className="source-ref">
                              <div>{item.source_file}</div>
                              <div>{item.source_sheet}</div>
                              <div>Row {item.source_row_index}</div>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="disclaimer">
                <strong>Disclaimer:</strong> {estimate.disclaimer}
              </div>
            </>
          )}
          
          {estimate.audit_log.length > 0 && (
            <div className="card">
              <h3>Audit Log</h3>
              <div className="audit-log">
                {estimate.audit_log.map((entry, idx) => (
                  <div key={idx} className="audit-entry">
                    <div><strong>{entry.action}</strong>: {entry.decision}</div>
                    <div>{entry.reason}</div>
                    {entry.source && <div className="source-ref">Source: {entry.source}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ConceptEstimate;
