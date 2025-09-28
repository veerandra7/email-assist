/**
 * Authentication status component - handles Gmail OAuth2 flow
 */
import React, { useState, useEffect } from 'react';
import Button from './ui/Button';
import Card from './ui/Card';
import LoadingSpinner from './ui/LoadingSpinner';
import { authAPI } from '../utils/auth';
import { handleAPIError } from '../utils/api';

interface AuthStatusProps {
  onAuthChange: (authenticated: boolean) => void;
}

interface UserProfile {
  email: string;
  messages_total: number;
  threads_total: number;
}

const AuthStatus: React.FC<AuthStatusProps> = ({ onAuthChange }) => {
  const [authenticated, setAuthenticated] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabId] = useState(() => {
    // Check if we're in browser environment
    if (typeof window !== 'undefined') {
      // First check if session ID is in URL params (from OAuth redirect)
      const urlParams = new URLSearchParams(window.location.search);
      const sessionFromUrl = urlParams.get('session_id');
      
      if (sessionFromUrl) {
        // Use session ID from OAuth redirect and store it
        sessionStorage.setItem('email_assist_tab_id', sessionFromUrl);
        // Clean URL after capturing session ID
        window.history.replaceState({}, document.title, window.location.pathname);
        return sessionFromUrl;
      }
      
      // Check if tab ID already exists in sessionStorage
      let existingTabId = sessionStorage.getItem('email_assist_tab_id');
      if (!existingTabId) {
        // Generate new unique tab ID for this browser tab
        existingTabId = 'tab_' + Math.random().toString(36).substr(2, 16) + '_' + Date.now();
        sessionStorage.setItem('email_assist_tab_id', existingTabId);
      }
      return existingTabId;
    }
    // Fallback for SSR - will be replaced once component mounts in browser
    return 'tab_ssr_' + Math.random().toString(36).substr(2, 8);
  });

  useEffect(() => {
    checkAuthStatus();
    
    // Check for auth callback in URL
    const urlParams = new URLSearchParams(window.location.search);
    const authResult = urlParams.get('auth');
    
    if (authResult === 'success') {
      window.history.replaceState({}, document.title, window.location.pathname);
      checkAuthStatus();
    } else if (authResult === 'error') {
      const message = urlParams.get('message') || 'Authentication failed';
      setError(message);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      // Use authAPI which ensures X-Tab-ID header is sent via axios interceptors
      const data = await authAPI.getStatus();
      
      setAuthenticated(data.authenticated);
      setUserProfile(data.user_profile || null);
      onAuthChange(data.authenticated);
      
      if (data.error) {
        setError(data.error);
      }
    } catch (err) {
      setError(handleAPIError(err));
      setAuthenticated(false);
      onAuthChange(false);
    } finally {
      setLoading(false);
    }
  };

  const initiateAuth = async () => {
    try {
      setAuthLoading(true);
      setError(null);
      
      // Use authAPI which ensures X-Tab-ID header is sent via axios interceptors
      const data = await authAPI.getAuthUrl();
      
      if (data.auth_url) {
        // Redirect to Gmail OAuth
        window.location.href = data.auth_url;
      } else {
        setError('Failed to get authentication URL');
      }
    } catch (err) {
      setError(handleAPIError(err));
    } finally {
      setAuthLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      // Use authAPI which ensures X-Tab-ID header is sent via axios interceptors
      await authAPI.logout();
      
      setAuthenticated(false);
      setUserProfile(null);
      onAuthChange(false);
      
      // Clear the tab ID so a fresh session is created on next use
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('email_assist_tab_id');
      }
    } catch (err) {
      setError(handleAPIError(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="text-center py-4">
        <LoadingSpinner size="sm" className="mx-auto mb-2" />
        <p className="text-sm text-gray-600">Checking authentication...</p>
      </Card>
    );
  }

  if (!authenticated) {
    return (
      <Card className="text-center py-6">
        <div className="mb-4">
          <div className="text-blue-600 mb-3">
            <svg className="mx-auto h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.25a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Connect Your Gmail
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Authenticate with Gmail to access your emails and enable AI-powered responses
          </p>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
          <Button 
            onClick={initiateAuth} 
            disabled={authLoading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {authLoading ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Connecting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Connect Gmail
              </>
            )}
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-green-600">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">
              {userProfile?.email || 'Connected'}
            </p>
            {userProfile && (
              <p className="text-xs text-gray-600">
                {userProfile.messages_total} emails • {userProfile.threads_total} threads
              </p>
            )}
          </div>
        </div>
        <Button 
          onClick={logout}
          variant="outline"
          size="sm"
        >
          Disconnect
        </Button>
      </div>
    </Card>
  );
};

export default AuthStatus; 