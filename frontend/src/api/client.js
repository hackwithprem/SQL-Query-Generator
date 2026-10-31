import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Attach JWT token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiClient = {
  // Auth
  login: async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    if (res.data?.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
    }
    return res.data;
  },

  signup: async (fullName, email, password) => {
    const res = await api.post('/auth/signup', { full_name: fullName, email, password });
    if (res.data?.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
    }
    return res.data;
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
    }
  },

  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data;
  },

  updateProfile: async (fullName) => {
    const res = await api.put('/auth/profile', { full_name: fullName });
    return res.data;
  },

  // Health & Core Schema
  getHealth: async () => {
    const res = await api.get('/health');
    return res.data;
  },

  getSchema: async () => {
    const res = await api.get('/schema');
    return res.data;
  },

  // SQL Operations
  generateSql: async (question, dialect = 'sqlite', datasetId = null, connectionId = null) => {
    const res = await api.post('/generate-sql', { 
      question, 
      dialect, 
      dataset_id: datasetId,
      connection_id: connectionId 
    });
    return res.data;
  },

  executeSql: async (sql, limit = 500, datasetId = null, connectionId = null) => {
    const res = await api.post('/execute-sql', { 
      sql, 
      limit, 
      dataset_id: datasetId,
      connection_id: connectionId 
    });
    return res.data;
  },

  explainSql: async (sql, question = '', datasetId = null, connectionId = null) => {
    const res = await api.post('/explain-sql', { 
      sql, 
      question, 
      dataset_id: datasetId,
      connection_id: connectionId 
    });
    return res.data;
  },

  correctSql: async (originalQuestion, failedSql, errorMessage, datasetId = null, connectionId = null) => {
    const res = await api.post('/correct-sql', {
      original_question: originalQuestion,
      failed_sql: failedSql,
      error_message: errorMessage,
      dataset_id: datasetId,
      connection_id: connectionId
    });
    return res.data;
  },

  // Query History
  getHistory: async (limit = 50) => {
    const res = await api.get('/history', { params: { limit } });
    return res.data;
  },

  clearHistory: async () => {
    const res = await api.post('/history/clear');
    return res.data;
  },

  // Upload Data (CSV & Excel)
  uploadData: async (file, sheetName = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (sheetName) {
      formData.append('sheet_name', sheetName);
    }
    const res = await api.post('/data/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  getFiles: async () => {
    const res = await api.get('/data/files');
    return res.data;
  },

  getFilePreview: async (fileId) => {
    const res = await api.get(`/data/files/${fileId}/preview`);
    return res.data;
  },

  deleteFile: async (fileId) => {
    const res = await api.delete(`/data/files/${fileId}`);
    return res.data;
  },

  renameDataset: async (fileId, newName) => {
    const res = await api.patch(`/data/files/${fileId}/rename`, { new_name: newName });
    return res.data;
  },

  // Cloud Database Connections
  testConnection: async (data) => {
    const res = await api.post('/connections/test', data);
    return res.data;
  },

  createConnection: async (data) => {
    const res = await api.post('/connections', data);
    return res.data;
  },

  getConnections: async () => {
    const res = await api.get('/connections');
    return res.data;
  },

  getConnectionSchema: async (connId) => {
    const res = await api.get(`/connections/${connId}/schema`);
    return res.data;
  },

  deleteConnection: async (connId) => {
    const res = await api.delete(`/connections/${connId}`);
    return res.data;
  },
};
