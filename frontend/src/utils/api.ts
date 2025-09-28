/**
 * API utility functions for backend communication.
 * Follows DRY principle - centralizes all API calls.
 */
import axios, { AxiosResponse, AxiosError } from 'axios';
import {
  EmailDomain,
  EmailContent,
  EmailSummary,
  ResponseRequest,
  ResponseGeneration,
  AIProvider,
  HealthStatus
} from '@/types/email';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 60000, // Increased to 60 seconds for slow Gmail API calls
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for session management
});

// Enhanced logging utility
const logAPI = {
  info: (message: string, data?: any) => {
    console.log(`🔵 [API] ${message}`, data ? data : '');
  },
  success: (message: string, data?: any) => {
    console.log(`✅ [API] ${message}`, data ? data : '');
  },
  error: (message: string, error?: any) => {
    console.error(`❌ [API] ${message}`, error ? error : '');
  },
  debug: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`🔍 [API] ${message}`, data ? data : '');
    }
  },
  timing: (operation: string, startTime: number) => {
    const duration = Date.now() - startTime;
    console.log(`⏱️ [API] ${operation} completed in ${duration}ms`);
  }
};

// Generate unique tab ID for this browser tab instance (persistent across page reloads)
const getTabId = (() => {
  let tabId: string | null = null;
  return () => {
    if (!tabId) {
      // Check if we're in browser environment
      if (typeof window !== 'undefined') {
        // First check if session ID is in URL params (from OAuth redirect)
        const urlParams = new URLSearchParams(window.location.search);
        const sessionFromUrl = urlParams.get('session_id');
        
        if (sessionFromUrl) {
          // Use session ID from OAuth redirect and store it
          tabId = sessionFromUrl;
          sessionStorage.setItem('email_assist_tab_id', tabId);
          return tabId;
        }
        
        // Check if tab ID already exists in sessionStorage
        tabId = sessionStorage.getItem('email_assist_tab_id');
        if (!tabId) {
          tabId = 'tab_' + Math.random().toString(36).substr(2, 16) + '_' + Date.now();
          sessionStorage.setItem('email_assist_tab_id', tabId);
        }
      } else {
        // Fallback for SSR
        tabId = 'tab_ssr_' + Math.random().toString(36).substr(2, 8);
      }
    }
    return tabId;
  };
})();

// Request interceptor for enhanced logging and tab ID injection
api.interceptors.request.use(
  (config) => {
    const startTime = Date.now();
    (config as any).metadata = { startTime };
    
    // Add tab ID header for session management
    config.headers.set('X-Tab-ID', getTabId());
    
    logAPI.info(`📤 Request: ${config.method?.toUpperCase()} ${config.url}`);
    logAPI.debug('Request config:', {
      url: config.url,
      method: config.method,
      headers: config.headers,
      data: config.data,
      timeout: config.timeout
    });
    
    return config;
  },
  (error: AxiosError) => {
    logAPI.error('Request setup error:', error.message);
    return Promise.reject(error);
  }
);

// Response interceptor for enhanced error handling and logging
api.interceptors.response.use(
  (response) => {
    const config = response.config as any;
    const duration = config.metadata ? Date.now() - config.metadata.startTime : 0;
    
    logAPI.success(`📥 Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url} (${duration}ms)`);
    logAPI.debug('Response data:', {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
      data: response.data
    });
    
    return response;
  },
  (error: AxiosError) => {
    const config = error.config as any;
    const duration = config?.metadata ? Date.now() - config.metadata.startTime : 0;
    
    if (error.response) {
      // Server responded with error status
      logAPI.error(`📥 Error Response: ${error.response.status} ${error.config?.method?.toUpperCase()} ${error.config?.url} (${duration}ms)`);
      logAPI.error('Response error details:', {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
        url: error.config?.url
      });
    } else if (error.request) {
      // Request made but no response received
      logAPI.error(`🌐 Network Error: No response received for ${error.config?.method?.toUpperCase()} ${error.config?.url} (${duration}ms)`);
      logAPI.error('Network error details:', {
        message: error.message,
        code: error.code,
        url: error.config?.url
      });
    } else {
      // Error in request setup
      logAPI.error(`⚙️ Request Setup Error: ${error.message}`);
    }
    
    return Promise.reject(error);
  }
);

// Email API functions with enhanced logging
export const emailAPI = {
  /**
   * Get all email domains with importance scores
   */
  getDomains: async (): Promise<EmailDomain[]> => {
    logAPI.info('📋 Fetching all email domains...');
    try {
      const response: AxiosResponse<EmailDomain[]> = await api.get('/api/emails/domains');
      logAPI.success(`Retrieved ${response.data.length} email domains`);
      logAPI.debug('Domains data:', response.data.map(d => ({ domain: d.domain, count: d.count, importance: d.importance_score })));
      return response.data;
    } catch (error) {
      logAPI.error('Failed to fetch email domains');
      throw error;
    }
  },

  /**
   * Get emails from a specific domain (subjects only for performance)
   */
  getEmailsByDomain: async (domain: string, limit = 20): Promise<EmailContent[]> => {
    logAPI.info(`📬 Fetching email subjects from domain: ${domain} (limit: ${limit})`);
    try {
      const response: AxiosResponse<EmailContent[]> = await api.get(
        `/api/emails/domains/${encodeURIComponent(domain)}/emails`,
        { params: { limit } }
      );
      logAPI.success(`Retrieved ${response.data.length} email subjects from domain ${domain}`);
      logAPI.debug('Email subjects:', response.data.map(e => ({ 
        subject: e.subject.substring(0, 50) + '...', 
        sender: e.sender,
        received_date: e.received_date,
        message_id: e.message_id 
      })));
      return response.data;
    } catch (error) {
      logAPI.error(`Failed to fetch emails from domain: ${domain}`);
      throw error;
    }
  },

  /**
   * Get full email content by message ID
   */
  getFullEmail: async (messageId: string): Promise<EmailContent> => {
    logAPI.info(`📧 Loading full email content for message: ${messageId}`);
    try {
      const response: AxiosResponse<EmailContent> = await api.get(
        `/api/emails/message/${encodeURIComponent(messageId)}`
      );
      logAPI.success(`Retrieved full email content: ${response.data.subject}`);
      logAPI.debug('Full email loaded:', {
        subject: response.data.subject,
        sender: response.data.sender,
        bodyLength: response.data.body.length
      });
      return response.data;
    } catch (error) {
      logAPI.error(`Failed to load full email for message: ${messageId}`);
      throw error;
    }
  },

  /**
   * Summarize an email using AI
   */
  summarizeEmail: async (email: EmailContent): Promise<EmailSummary> => {
    logAPI.info(`🤖 Summarizing email: "${email.subject}" from ${email.sender}`);
    try {
      const startTime = Date.now();
      const response: AxiosResponse<EmailSummary> = await api.post('/api/emails/summarize', email);
      const duration = Date.now() - startTime;
      
      logAPI.success(`Email summarization completed in ${duration}ms`);
      logAPI.debug('Summary result:', {
        summary: response.data.summary.substring(0, 100) + '...',
        urgency_level: response.data.urgency_level,
        action_required: response.data.action_required,
        key_points_count: response.data.key_points.length
      });
      
      return response.data;
    } catch (error) {
      logAPI.error(`Failed to summarize email: "${email.subject}"`);
      throw error;
    }
  },

  /**
   * Generate an email response using AI
   */
  generateResponse: async (request: ResponseRequest): Promise<ResponseGeneration> => {
    logAPI.info(`✍️ Generating response for email: "${request.original_email.subject}"`);
    logAPI.debug('Generation request:', {
      user_input: request.user_input,
      tone: request.tone,
      original_subject: request.original_email.subject
    });
    
    try {
      const startTime = Date.now();
      const response: AxiosResponse<ResponseGeneration> = await api.post(
        '/api/emails/generate-response',
        request
      );
      const duration = Date.now() - startTime;
      
      logAPI.success(`Response generation completed in ${duration}ms`);
      logAPI.debug('Generated response:', {
        response_length: response.data.generated_response.length,
        confidence_score: response.data.confidence_score
      });
      
      return response.data;
    } catch (error) {
      logAPI.error(`Failed to generate response for email: "${request.original_email.subject}"`);
      throw error;
    }
  },

  /**
   * Health check for email service
   */
  healthCheck: async (): Promise<HealthStatus> => {
    logAPI.info('🩺 Checking email service health...');
    try {
      const response: AxiosResponse<HealthStatus> = await api.get('/api/emails/health');
      logAPI.success(`Email service health: ${response.data.status}`);
      return response.data;
    } catch (error) {
      logAPI.error("Email service health check failed");
      throw error;
    }
  },  /**
   * Send email reply
   */
  sendReply: async (originalEmail: EmailContent, replyBody: string): Promise<{message: string}> => {
    logAPI.info(`📤 Sending reply for email: "${originalEmail.subject}"`);
    logAPI.debug("Send reply request:", {
      original_subject: originalEmail.subject,
      original_sender: originalEmail.sender,
      reply_length: replyBody.length
    });
    
    try {
      const startTime = Date.now();
      const response: AxiosResponse<{message: string}> = await api.post(
        "/api/emails/send-reply",
        {
          original_email: originalEmail,
          reply_body: replyBody
        }
      );
      const duration = Date.now() - startTime;
      
      logAPI.success(`Reply sent successfully in ${duration}ms`);
      logAPI.debug("Send reply response:", {
        message: response.data.message
      });
      
      return response.data;
    } catch (error) {
      logAPI.error(`Failed to send reply for email: "${originalEmail.subject}"`);
      throw error;
    }
  },
};
// AI API functions with enhanced logging
export const aiAPI = {
  /**
   * Get current AI provider information
   */
  getProvider: async (): Promise<AIProvider> => {
    logAPI.info('🤖 Fetching AI provider information...');
    try {
      const response: AxiosResponse<AIProvider> = await api.get('/api/ai/provider');
      logAPI.success(`AI provider: ${response.data.provider} (${response.data.status})`);
      return response.data;
    } catch (error) {
      logAPI.error('Failed to fetch AI provider information');
      throw error;
    }
  },

  /**
   * Health check for AI service
   */
  healthCheck: async (): Promise<HealthStatus> => {
    logAPI.info('🩺 Checking AI service health...');
    try {
      const response: AxiosResponse<HealthStatus> = await api.get('/api/ai/health');
      logAPI.success(`AI service health: ${response.data.status}`);
      return response.data;
    } catch (error) {
      logAPI.error('AI service health check failed');
      throw error;
    }
  },
};

// Enhanced error handling utilities
export const handleAPIError = (error: any): string => {
  logAPI.error('Handling API error:', error);
  
  if (error.response?.data?.detail) {
    logAPI.debug('Error details from server:', error.response.data);
    return error.response.data.detail;
  }
  
  if (error.response?.status === 503) {
    logAPI.error('Service unavailable (503)');
    return 'Service temporarily unavailable. Please check your API keys and try again.';
  }
  
  if (error.response?.status >= 500) {
    logAPI.error(`Server error (${error.response.status})`);
    return 'Server error. Please try again later.';
  }
  
  if (error.request) {
    logAPI.error('Network error - no response received');
    if (error.code === 'ECONNABORTED') {
      return 'Request timed out. Gmail API is slow, please try again.';
    }
    return 'Network error. Please check your connection and try again.';
  }
  
  logAPI.error('Unknown error type');
  return error.message || 'An unexpected error occurred.';
};

// Export the logging utility for use in components
export { logAPI };

export default api; 