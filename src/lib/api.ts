import axios from 'axios';
import {
  ForecastRequest,
  ForecastResponse,
  ForecastStatus,
  ForecastResult
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/.netlify/functions';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor for auth
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Get available models
  getModels: async () => {
    const response = await apiClient.get('/api/models');
    return response.data;
  },

  // Create a new forecast
  createForecast: async (request: ForecastRequest): Promise<ForecastResponse> => {
    const response = await apiClient.post('/api/forecast', request);
    return response.data;
  },

  // Get forecast status
  getForecastStatus: async (forecastId: string): Promise<ForecastStatus> => {
    const response = await apiClient.get(`/api/forecast/${forecastId}`);
    return response.data;
  },

  // Download Excel report
  downloadExcel: async (forecastId: string): Promise<Blob> => {
    const response = await apiClient.get(`/api/forecast/${forecastId}/excel`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Cancel a forecast
  cancelForecast: async (forecastId: string): Promise<void> => {
    await apiClient.post(`/api/forecast/${forecastId}/cancel`);
  },

  // List forecasts
  listForecasts: async (userId?: string, limit = 10, offset = 0) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await apiClient.get(`/api/forecasts?${params.toString()}`);
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/api/health');
    return response.data;
  },
};

// Export download helper
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default api;