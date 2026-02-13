import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// File upload
export const uploadFile = async (file: File, fileType: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('file_type', fileType);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Config
export const getConfigSummary = async () => {
  const response = await api.get('/config/summary');
  return response.data;
};

// Projects
export const createProject = async (projectData: any) => {
  const response = await api.post('/projects', projectData);
  return response.data;
};

export const getProject = async (projectId: string) => {
  const response = await api.get(`/projects/${projectId}`);
  return response.data;
};

export const evaluateProject = async (projectId: string) => {
  const response = await api.post(`/projects/${projectId}/evaluate`);
  return response.data;
};

// Rates
export const searchRates = async (request: {
  rate_library: string;
  search_text: string;
  sheet?: string;
}) => {
  const response = await api.post('/rates/search', request);
  return response.data;
};

// Estimates
export const calculateConceptEstimate = async (projectId: string) => {
  const response = await api.post(`/estimate/concept?project_id=${projectId}`);
  return response.data;
};

// Health check
export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE_URL.replace('/api', '')}/health`);
  return response.data;
};
