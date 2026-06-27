import axios from 'axios';

/**
 * Robust Data Service for OrionLedger / Mushtari
 * Centralizes all API calls, error handling, and response parsing.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15s timeout
});

/**
 * Standardized error handler
 * @param {Error} error 
 */
const handleError = (error) => {
  if (error.response) {
    // Server responded with a status code out of range of 2xx
    console.error('API Error Response:', error.response.data);
    throw new Error(error.response.data.detail || error.response.data.message || 'Server error occurred');
  } else if (error.request) {
    // Request was made but no response received
    console.error('API Network Error:', error.request);
    throw new Error('Network error: No response from server. Is the backend running?');
  } else {
    // Something happened in setting up the request
    console.error('API Request Error:', error.message);
    throw error;
  }
};

const dataService = {
  // ── AI & ML Operations (formerly aiService) ────────────────────────────────

  /**
   * Fetch all registered products from the database.
   */
  async getProducts() {
    try {
      const response = await api.get('/api/products');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch full details for a single product.
   */
  async getProductById(productId) {
    try {
      const response = await api.get(`/api/products/${productId}`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch historical sales for a specific product.
   */
  async getProductSales(productId, scope = 'day', startDate = null, endDate = null) {
    try {
      const params = { scope };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      const response = await api.get(`/api/products/${productId}/sales`, { params });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Predict demand for a specific product using XGBoost.
   * @param {object} payload - { product_id, horizon, scope, ... }
   */
  async predictDemand(payload) {
    try {
      const response = await api.post('/api/predict', payload);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get ARIMA-based forecast for a product, aggregated to the requested scope.
   * @param {number} productId
   * @param {number} horizon - number of periods at the requested scope
   * @param {string} scope - day, week, month, year, 5years, beginning
   */
  async getForecast(productId, horizon = 7) {
    try {
      const response = await api.get(`/api/forecast`, {
        params: { product_id: productId, horizon }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Generate import/ordering insights for a product using LLM.
   */
  async getInsight(productId, scope = 'week', horizon = 4) {
    try {
      const response = await api.get(`/api/products/${productId}/insight`, {
        params: { scope, horizon }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ── Analytics & Stats ──────────────────────────────────────────────────

  /**
   * Fetch high-level business KPIs.
   */
  async getKPIs() {
    try {
      const response = await api.get('/api/analytics/kpis');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch aggregated demand data for charts.
   */
  async getAggregatedDemand(scope = 'week') {
    try {
      const response = await api.get('/api/analytics/demand', {
        params: { scope }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch active system alerts.
   */
  async getSystemAlerts(severity = 'all', includeResolved = false) {
    try {
      const response = await api.get('/api/analytics/alerts', {
        params: { severity, include_resolved: includeResolved }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Resolve a system alert.
   */
  async resolveAlert(alertId, severity, ts) {
    try {
      const response = await api.post('/api/analytics/alerts/resolve', {
        alert_id: alertId,
        severity: severity,
        ts: ts
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Mark all unresolved alerts as resolved (archived).
   */
  async markAllAlertsRead() {
    try {
      const response = await api.post('/api/analytics/alerts/mark-all-read');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Perform backend health check.
   */
  async getHealth() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ── Data Import ───────────────────────────────────────────────────────

  /**
   * Upload an Excel file to import products.
   * @param {File} file - The .xlsx file
   * @param {function} onProgress - Optional callback for upload progress
   */
  async importProducts(file, onProgress) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post('/api/import/products', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000, // 2 min for large imports
        onUploadProgress: onProgress,
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Upload an Excel file to import orders and sales.
   * @param {File} file - The .xlsx file
   * @param {function} onProgress - Optional callback for upload progress
   */
  async importOrders(file, onProgress) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post('/api/import/orders', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
        onUploadProgress: onProgress,
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Download a products import template.
   */
  async getProductsTemplate() {
    try {
      const response = await api.get('/api/import/template/products');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Download an orders import template.
   */
  async getOrdersTemplate() {
    try {
      const response = await api.get('/api/import/template/orders');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get the download URL for a template file.
   */
  getTemplateDownloadUrl(type) {
    return `${API_BASE_URL}/api/import/template/${type}/file`;
  },

};

export default dataService;
