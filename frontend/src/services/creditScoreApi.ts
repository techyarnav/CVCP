export interface CreditScoreResponse {
  success: boolean;
  address: string;
  credit_score: {
    totalScore: number;
    transactionScore: number;
    defiScore: number;
    stakingScore: number;
    riskScore: number;
    historyScore: number;
    confidence: number;
    lastUpdated: number;
    updateCount: number;
    isActive: boolean;
  } | null;
  contract_transactions: Record<string, any>;
  processing_time_seconds: number;
  ai_analysis: {
    rating: string;
    risk_level: string;
    score: number;
    recommendation: string;
    summary: string;
  } | null;
  rate_limited: boolean;
  cache_used: boolean;
  error: string | null;
  timestamp: string;
}

export interface CalculateScoreRequest {
  address: string;
  force_refresh: boolean;
}

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error);
    return Promise.reject(error);
  }
);

export const creditScoreApi = {
  async calculateScore(request: CalculateScoreRequest): Promise<CreditScoreResponse> {
    try {
      const response = await apiClient.post('/api/calculate-score', request);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response) {
          // Server responded with error status
          throw new Error(`Server error: ${error.response.status} - ${error.response.data?.error || error.response.statusText}`);
        } else if (error.request) {
          // Request was made but no response received
          throw new Error('No response received from server. Please check if the backend is running.');
        } else {
          // Something else happened
          throw new Error(`Request error: ${error.message}`);
        }
      } else {
        // Non-axios error
        throw new Error(`Unexpected error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  },

  async checkBackendHealth(): Promise<boolean> {
    try {
      await apiClient.get('/health');
      return true;
    } catch (error) {
      console.warn('Backend health check failed:', error);
      return false;
    }
  },

  async getBackendStatus(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await apiClient.get('/status');
      return response.data;
    } catch (error) {
      throw new Error('Unable to get backend status');
    }
  },
}; 