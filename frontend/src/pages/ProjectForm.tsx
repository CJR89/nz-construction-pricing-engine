import React, { useState } from 'react';
import { createProject, evaluateProject } from '../services/api';
import type { ProjectInput, EngineOutput } from '../types';

const ProjectForm: React.FC = () => {
  const [formData, setFormData] = useState<ProjectInput>({
    project_id: '',
    project_stage: 'Concept',
    building_type: '',
    location_city: '',
    gfa_m2: undefined,
    shell_only: false,
    fitout_required: false,
    fitout_allowance_per_m2: undefined,
  });
  
  const [evaluation, setEvaluation] = useState<EngineOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      setFormData({
        ...formData,
        [name]: (e.target as HTMLInputElement).checked,
      });
    } else if (type === 'number') {
      setFormData({
        ...formData,
        [name]: value ? parseFloat(value) : undefined,
      });
    } else {
      setFormData({
        ...formData,
        [name]: value,
      });
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setEvaluation(null);
    
    try {
      await createProject(formData);
      setSuccess(`Project ${formData.project_id} created successfully!`);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };
  
  const handleEvaluate = async () => {
    setError(null);
    setEvaluation(null);
    
    try {
      const result = await evaluateProject(formData.project_id);
      setEvaluation(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };
  
  return (
    <div>
      <h2>Create Project</h2>
      
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}
      
      <form onSubmit={handleSubmit} className="card">
        <div className="form-group">
          <label>Project ID *</label>
          <input
            type="text"
            name="project_id"
            value={formData.project_id}
            onChange={handleChange}
            required
            placeholder="e.g., PROJ-001"
          />
        </div>
        
        <div className="form-group">
          <label>Project Stage *</label>
          <select
            name="project_stage"
            value={formData.project_stage}
            onChange={handleChange}
            required
          >
            <option value="Concept">Concept</option>
            <option value="Preliminary">Preliminary</option>
            <option value="Developed">Developed</option>
            <option value="Detailed">Detailed</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>Building Type *</label>
          <input
            type="text"
            name="building_type"
            value={formData.building_type}
            onChange={handleChange}
            placeholder="e.g., Office, Warehouse, Residential"
          />
        </div>
        
        <div className="form-group">
          <label>Location City *</label>
          <select
            name="location_city"
            value={formData.location_city}
            onChange={handleChange}
          >
            <option value="">Select city...</option>
            <option value="Auckland">Auckland</option>
            <option value="Wellington">Wellington</option>
            <option value="Christchurch">Christchurch</option>
            <option value="Hamilton">Hamilton</option>
            <option value="Tauranga">Tauranga</option>
            <option value="Dunedin">Dunedin</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>GFA (m²) *</label>
          <input
            type="number"
            name="gfa_m2"
            value={formData.gfa_m2 || ''}
            onChange={handleChange}
            placeholder="e.g., 5000"
            step="0.01"
          />
        </div>
        
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="shell_only"
              checked={formData.shell_only}
              onChange={handleChange}
            />
            Shell Only
          </label>
        </div>
        
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="fitout_required"
              checked={formData.fitout_required}
              onChange={handleChange}
            />
            Fitout Required
          </label>
        </div>
        
        {formData.shell_only && formData.fitout_required && (
          <div className="form-group">
            <label>Fitout Allowance ($/m²)</label>
            <input
              type="number"
              name="fitout_allowance_per_m2"
              value={formData.fitout_allowance_per_m2 || ''}
              onChange={handleChange}
              placeholder="e.g., 500"
              step="0.01"
            />
          </div>
        )}
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" className="button">
            Create Project
          </button>
          
          {success && (
            <button
              type="button"
              className="button button-secondary"
              onClick={handleEvaluate}
            >
              Evaluate Project
            </button>
          )}
        </div>
      </form>
      
      {evaluation && (
        <div className="card">
          <h3>Evaluation Results</h3>
          
          {evaluation.blocked_reason ? (
            <div className="alert alert-error">
              <strong>BLOCKED:</strong> {evaluation.blocked_reason}
              
              {evaluation.required_missing_inputs.length > 0 && (
                <div style={{ marginTop: '10px' }}>
                  <strong>Missing inputs:</strong>
                  <ul>
                    {evaluation.required_missing_inputs.map((input) => (
                      <li key={input}>{input}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="alert alert-success">
              <strong>Success!</strong> Can proceed with pricing.
              <div style={{ marginTop: '10px' }}>
                <strong>Primary Library:</strong> {evaluation.selected_primary_library}
                {evaluation.selected_secondary_library && (
                  <div><strong>Secondary Library:</strong> {evaluation.selected_secondary_library}</div>
                )}
              </div>
            </div>
          )}
          
          <div className="alert alert-info">
            <strong>Next Action:</strong> {evaluation.next_action}
          </div>
          
          <h4>Audit Log</h4>
          <div className="audit-log">
            {evaluation.audit_log.map((entry, idx) => (
              <div key={idx} className="audit-entry">
                <div><strong>{entry.action}</strong>: {entry.decision}</div>
                <div>{entry.reason}</div>
                {entry.source && <div className="source-ref">Source: {entry.source}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectForm;
