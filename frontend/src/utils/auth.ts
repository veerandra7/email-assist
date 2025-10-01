/**
 * Authentication API utilities using configured axios instance
 */
import api from './api';

export interface AuthStatus {
  authenticated: boolean;
  user_profile?: {
    email: string;
    messages_total: number;
    threads_total: number;
  };
  error?: string;
}

export interface AuthUrlResponse {
  auth_url: string;
}

export const authAPI = {
  /**
   * Check Gmail authentication status
   */
  getStatus: async (): Promise<AuthStatus> => {
    const response = await api.get('/auth/gmail/status');
    return response.data;
  },

  /**
   * Get Gmail OAuth URL
   */
  getAuthUrl: async (): Promise<AuthUrlResponse> => {
    const response = await api.get('/auth/gmail/url');
    return response.data;
  },

  /**
   * Logout from Gmail
   */
  logout: async (): Promise<{ message: string }> => {
    const response = await api.post('/auth/gmail/logout');
    return response.data;
  }
}; 