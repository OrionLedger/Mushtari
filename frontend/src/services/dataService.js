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
   * Predict demand for a specific product using XGBoost.
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
   * Predict batch demand for multiple products.
   */
  async predictBatch(payload) {
    try {
      const response = await api.post('/api/predict/batch', payload);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get ARIMA-based forecast for a product.
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
   * Retrain an XGBoost model for a product.
   */
  async trainModel(payload) {
    try {
      const response = await api.patch('/api/train/xgboost', payload);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch Market Fit KPIs.
   */
  async getMarketFitKPIs(payload) {
    try {
      const response = await api.post('/api/kpi/market-fit', payload);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Trigger the ETL pipeline extraction.
   */
  async triggerETL(payload) {
    try {
      const response = await api.post(`/api/data/extract`, payload);
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
   * Fetch revenue breakdown by category (product, country, channel).
   */
  async getBreakdown(category = 'product') {
    try {
      const response = await api.get('/api/analytics/breakdown', {
        params: { category }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch user statistics by category (device, source).
   */
  async getUserStats(category = 'device') {
    try {
      const response = await api.get('/api/analytics/users', {
        params: { category }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ── Data Sources Registry ──────────────────────────────────────────────────

  /**
   * List all saved data source connections.
   */
  async getSources() {
    try {
      const response = await api.get('/api/sources');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Persist a new data source connection.
   * @param {{ name, source_type, conn_uri }} payload
   */
  async addSource(payload) {
    try {
      const response = await api.post('/api/sources', payload);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Delete a data source by ID.
   */
  async deleteSource(id) {
    try {
      const response = await api.delete(`/api/sources/${id}`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Test a connection URI without saving it.
   * Returns { ok: bool, message: string }
   */
  async testConnection(conn_uri) {
    try {
      const response = await api.post('/api/sources/test', { conn_uri });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Trigger an ETL sync job for a registered source.
   */
  async syncSource(id) {
    try {
      const response = await api.post(`/api/sources/${id}/sync`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Trigger parallel sync for all sources.
   */
  async syncAllSources() {
    try {
      const response = await api.post(`/api/sources/sync-all`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch all tables available in a specific source.
   */
  async getSourceTables(id) {
    try {
      const response = await api.get(`/api/sources/${id}/tables`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch columns for a specific table in a source.
   */
  async getSourceSchema(id, tableName) {
    try {
      const response = await api.get(`/api/sources/${id}/schema`, {
        params: { table_name: tableName }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Update the table mapping for a source.
   */
  async updateSourceMapping(id, tableName, mapping, itemsSourceType = 'json_column', itemsTableName = null, interval = 6) {
    try {
      const response = await api.put(`/api/sources/${id}/mapping`, {
        table_name: tableName,
        mapping: mapping,
        items_source_type: itemsSourceType,
        items_table_name: itemsTableName,
        sync_interval_hours: interval
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch inventory / SKU overview.
   */
  async getInventory(query = '') {
    try {
      const response = await api.get('/api/analytics/inventory', {
        params: { query }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch active system alerts.
   */
  async getSystemAlerts(severity = 'all') {
    try {
      const response = await api.get('/api/analytics/alerts', {
        params: { severity }
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch generated reports.
   */
  async getReports() {
    try {
      const response = await api.get('/api/analytics/reports');
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
   * Trigger on-demand report generation.
   */
  async generateReport(payload) {
    try {
      const response = await api.post('/api/analytics/reports', payload);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Delete a report by ID.
   */
  async deleteReport(id) {
    try {
      const response = await api.delete(`/api/analytics/reports/${id}`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Fetch educational library content.
   */
  async getLibraryData() {
    try {
      const response = await api.get('/api/analytics/library');
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

};

export default dataService;
