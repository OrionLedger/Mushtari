import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Adjust if your backend runs on a different port

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const aiService = {
  // Demand Prediction (XGBoost)
  predictDemand: async (payload) => {
    // payload: { product_id, features: [], start_date, end_date }
    const response = await api.post('/api/predict', payload);
    return response.data;
  },

  // Batch Prediction
  predictBatch: async (payload) => {
    // payload: { product_ids: [], features: [], start_date, end_date }
    const response = await api.post('/api/predict/batch', payload);
    return response.data;
  },

  // ARIMA Forecasting
  getForecast: async (productId, horizon = 7) => {
    const response = await api.get(`/api/forecast?product_id=${productId}&horizon=${horizon}`);
    return response.data;
  },

  // Model Retraining
  trainModel: async (payload) => {
    // payload: { product_id, columns: [], start_date, end_date, test_size }
    const response = await api.patch('/api/train/xgboost', payload);
    return response.data;
  },

  // Market Fit KPIs
  getMarketFitKPIs: async (payload) => {
    const response = await api.post('/api/kpi/market-fit', payload);
    return response.data;
  },

  // ETL Extraction
  triggerETL: async (dbType = 'cassandra') => {
    const response = await api.post(`/api/data/extract?db_type=${dbType}`);
    return response.data;
  },

  // Health Check
  getHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  }
};

export default api;
