import React, { useState, useEffect } from 'react';
import { uploadFile, checkHealth } from '../services/api';
import type { FileUploadResponse } from '../types';

const FileUpload: React.FC = () => {
  const [files, setFiles] = useState<Record<string, File | null>>({
    master: null,
    bcm2: null,
    elem: null,
    cpr: null,
    det: null,
  });
  
  const [uploadStatus, setUploadStatus] = useState<Record<string, FileUploadResponse | null>>({
    master: null,
    bcm2: null,
    elem: null,
    cpr: null,
    det: null,
  });
  
  const [healthStatus, setHealthStatus] = useState<any>(null);
  
  const fileDescriptions = {
    master: 'Master Knowledge Base (Construction_Knowledge_Base_FINALIZED_WITH_SCHEMA.xlsm)',
    bcm2: 'Building Costs m2 NZ (Building Costs m2 NZ.xlsm)',
    elem: 'Elemental Costs NZ (Elemental Costs of Building NZ.xlsm)',
    cpr: 'CostPlan Rates (CostPlan NZ Rates.xlsx)',
    det: 'Detailed Rates (Detailed Rates NZ.xlsm)',
  };
  
  useEffect(() => {
    loadHealth();
  }, []);
  
  const loadHealth = async () => {
    try {
      const health = await checkHealth();
      setHealthStatus(health);
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };
  
  const handleFileChange = (fileType: string, file: File | null) => {
    setFiles({ ...files, [fileType]: file });
  };
  
  const handleUpload = async (fileType: string) => {
    const file = files[fileType];
    if (!file) return;
    
    try {
      const result = await uploadFile(file, fileType);
      setUploadStatus({ ...uploadStatus, [fileType]: result });
      await loadHealth();
    } catch (error: any) {
      setUploadStatus({
        ...uploadStatus,
        [fileType]: {
          file_type: fileType,
          filename: file.name,
          status: 'error',
          message: error.response?.data?.detail || error.message,
        },
      });
    }
  };
  
  const allFilesUploaded = healthStatus?.files_uploaded || false;
  
  return (
    <div>
      <h2>File Upload</h2>
      
      {healthStatus && (
        <div className={`alert ${allFilesUploaded ? 'alert-success' : 'alert-warning'}`}>
          {allFilesUploaded ? (
            <strong>✓ All required files uploaded. You can proceed to create projects.</strong>
          ) : (
            <strong>⚠ Please upload all required Excel files before proceeding.</strong>
          )}
        </div>
      )}
      
      {Object.keys(files).map((fileType) => {
        const status = uploadStatus[fileType];
        const uploaded = status?.status === 'success';
        
        return (
          <div key={fileType} className="card">
            <h3>{fileDescriptions[fileType as keyof typeof fileDescriptions]}</h3>
            
            <div className="form-group">
              <input
                type="file"
                accept=".xlsm,.xlsx"
                onChange={(e) => handleFileChange(fileType, e.target.files?.[0] || null)}
              />
            </div>
            
            <button
              className="button"
              onClick={() => handleUpload(fileType)}
              disabled={!files[fileType]}
            >
              Upload {fileType.toUpperCase()}
            </button>
            
            {status && (
              <div className={`alert ${uploaded ? 'alert-success' : 'alert-error'}`} style={{ marginTop: '10px' }}>
                {status.message}
                {uploaded && <div className="source-ref">File: {status.filename}</div>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default FileUpload;
