import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const apiClient = {
  getHealth: async () => {
    const res = await api.get('/health');
    return res.data;
  },

  getSchema: async () => {
    const res = await api.get('/schema');
    return res.data;
  },

  generateSql: async (question, dialect = 'sqlite') => {
    const res = await api.post('/generate-sql', { question, dialect });
    return res.data;
  },

  executeSql: async (sql, limit = 500) => {
    const res = await api.post('/execute-sql', { sql, limit });
    return res.data;
  },

  explainSql: async (sql, question = '') => {
    const res = await api.post('/explain-sql', { sql, question });
    return res.data;
  },

  correctSql: async (originalQuestion, failedSql, errorMessage) => {
    const res = await api.post('/correct-sql', {
      original_question: originalQuestion,
      failed_sql: failedSql,
      error_message: errorMessage,
    });
    return res.data;
  },

  getHistory: async (limit = 50) => {
    const res = await api.get('/history', { params: { limit } });
    return res.data;
  },

  clearHistory: async () => {
    const res = await api.post('/history/clear');
    return res.data;
  },
};
