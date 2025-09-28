/**
 * Main page component - Email AI Assistant
 */
'use client';

import React, { useState, useEffect } from 'react';
import { EmailContent } from '../types/email';
import AuthStatus from '../components/AuthStatus';
import DomainList from '../components/DomainList';
import EmailList from '../components/EmailList';
import EmailViewer from '../components/EmailViewer';

// Enhanced logging utility for components
const logComponent = {
  info: (message: string, data?: any) => {
    console.log(`🔵 [HomePage] ${message}`, data ? data : '');
  },
  debug: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`🔍 [HomePage] ${message}`, data ? data : '');
    }
  },
  user: (message: string, data?: any) => {
    console.log(`👤 [HomePage] User Action: ${message}`, data ? data : '');
  },
  state: (message: string, data?: any) => {
    console.log(`🔄 [HomePage] State Change: ${message}`, data ? data : '');
  }
};

export default function HomePage() {
  const [authenticated, setAuthenticated] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [selectedEmail, setSelectedEmail] = useState<EmailContent | undefined>(undefined);

  // Component lifecycle logging
  useEffect(() => {
    logComponent.info('🚀 HomePage component mounted');
    logComponent.debug('Initial state:', {
      authenticated,
      selectedDomain,
      selectedEmail: selectedEmail?.subject || 'none'
    });
    
    return () => {
      logComponent.info('🔥 HomePage component will unmount');
    };
  }, []);

  // State change logging
  useEffect(() => {
    logComponent.state(`Authentication status: ${authenticated ? 'authenticated' : 'not authenticated'}`);
  }, [authenticated]);

  useEffect(() => {
    logComponent.state(`Domain selection: ${selectedDomain || 'none selected'}`, { domain: selectedDomain });
  }, [selectedDomain]);

  useEffect(() => {
    logComponent.state(`Email selection: ${selectedEmail ? `"${selectedEmail.subject}" from ${selectedEmail.sender}` : 'none selected'}`, {
      subject: selectedEmail?.subject,
      sender: selectedEmail?.sender,
      domain: selectedEmail?.domain
    });
  }, [selectedEmail]);

  const handleDomainSelect = (domain: string) => {
    logComponent.user(`Selected domain: ${domain}`);
    logComponent.debug('Domain selection details:', { 
      previousDomain: selectedDomain,
      newDomain: domain,
      willClearEmail: !!selectedEmail
    });
    
    setSelectedDomain(domain);
    setSelectedEmail(undefined); // Clear selected email when domain changes
    
    logComponent.info(`Domain changed to: ${domain}, email selection cleared`);
  };

  const handleEmailSelect = (email: EmailContent) => {
    logComponent.user(`Selected email: "${email.subject}" from ${email.sender}`);
    logComponent.debug('Email selection details:', {
      subject: email.subject,
      sender: email.sender,
      domain: email.domain,
      receivedDate: email.received_date,
      priority: email.priority
    });
    
    setSelectedEmail(email);
    logComponent.info(`Email selected: ${email.subject}`);
  };

  const handleAuthChange = (isAuthenticated: boolean) => {
    logComponent.user(`Authentication ${isAuthenticated ? 'successful' : 'cleared'}`);
    logComponent.debug('Auth change details:', {
      previousAuth: authenticated,
      newAuth: isAuthenticated,
      willClearSelections: !isAuthenticated && (selectedDomain || selectedEmail)
    });
    
    setAuthenticated(isAuthenticated);
    
    if (!isAuthenticated) {
      logComponent.info('Clearing selections due to authentication loss');
      setSelectedDomain('');
      setSelectedEmail(undefined);
    }
  };

  // Render logging
  logComponent.debug('Rendering HomePage', {
    authenticated,
    selectedDomain,
    hasSelectedEmail: !!selectedEmail,
    timestamp: new Date().toISOString()
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                📧 Email AI Assistant
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                AI-powered email management and response system
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Authentication Status */}
        <div className="mb-8">
          <AuthStatus onAuthChange={handleAuthChange} />
        </div>

        {authenticated ? (
          <div className="space-y-6">
            {/* Tab Navigation */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6" aria-label="Tabs">
                  <button
                    className={`py-4 px-1 border-b-2 font-medium text-sm ${
                      !selectedDomain && !selectedEmail
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                    onClick={() => {
                      setSelectedDomain('');
                      setSelectedEmail(undefined);
                    }}
                  >
                    📧 Email Domains
                  </button>
                  
                  {selectedDomain && (
                    <button
                      className={`py-4 px-1 border-b-2 font-medium text-sm ${
                        selectedDomain && !selectedEmail
                          ? 'border-primary-500 text-primary-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedEmail(undefined)}
                    >
                      📬 {selectedDomain} Emails
                    </button>
                  )}
                  
                  {selectedEmail && (
                    <button
                      className="py-4 px-1 border-b-2 border-primary-500 text-primary-600 font-medium text-sm"
                    >
                      📄 {selectedEmail.subject.length > 30 ? selectedEmail.subject.substring(0, 30) + '...' : selectedEmail.subject}
                    </button>
                  )}
                </nav>
              </div>
              
              {/* Tab Content */}
              <div className="p-6">
                {!selectedDomain ? (
                  /* Domain List Tab */
                  <DomainList
                    onDomainSelect={handleDomainSelect}
                    selectedDomain={selectedDomain}
                  />
                ) : !selectedEmail ? (
                  /* Email List Tab */
                  <EmailList
                    domain={selectedDomain}
                    onEmailSelect={handleEmailSelect}
                    selectedEmail={selectedEmail}
                  />
                ) : (
                  /* Email Viewer Tab */
                  <EmailViewer email={selectedEmail} />
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Gmail Authentication Required
            </h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Please authenticate with your Gmail account above to access your emails and use AI-powered features.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Email AI Assistant v1.0.0
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>Powered by AI</span>
              <span>•</span>
              <span>Built with React & FastAPI</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
} 