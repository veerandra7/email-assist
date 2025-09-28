/**
 * Email list component - displays emails from a selected domain
 */
import React, { useState, useEffect } from 'react';
import { EmailContent, EmailPriority } from '../types/email';
import { emailAPI, handleAPIError } from '../utils/api';
import Button from './ui/Button';
import Card from './ui/Card';
import LoadingSpinner from './ui/LoadingSpinner';

interface EmailListProps {
  domain: string;
  onEmailSelect: (email: EmailContent) => void;
  selectedEmail?: EmailContent;
}

const EmailList: React.FC<EmailListProps> = ({ domain, onEmailSelect, selectedEmail }) => {
  const [emails, setEmails] = useState<EmailContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log(`🔍 [EmailList] Domain changed to: ${domain}`);
    if (domain) {
      loadEmails();
    } else {
      console.log('🔍 [EmailList] No domain selected, clearing emails');
      setEmails([]);
    }
  }, [domain]);

  const loadEmails = async () => {
    console.log(`📬 [EmailList] Loading emails for domain: ${domain}`);
    try {
      setLoading(true);
      setError(null);
      const data = await emailAPI.getEmailsByDomain(domain);
      console.log(`✅ [EmailList] Received ${data.length} emails for domain: ${domain}`);
      setEmails(data);
    } catch (err) {
      console.error(`❌ [EmailList] Failed to load emails for domain: ${domain}`, err);
      setError(handleAPIError(err));
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: EmailPriority) => {
    switch (priority) {
      case EmailPriority.URGENT:
        return 'text-red-600 bg-red-50 border-red-200';
      case EmailPriority.HIGH:
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case EmailPriority.MEDIUM:
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case EmailPriority.LOW:
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <Card className="text-center py-8">
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <p className="text-gray-600">Loading emails from {domain}...</p>
        <p className="text-sm text-gray-500 mt-2">Gmail API can be slow, please wait...</p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="text-center py-8">
        <div className="text-red-600 mb-4">
          <p className="font-medium">Failed to load emails</p>
          <p className="text-sm">{error}</p>
        </div>
        <Button onClick={loadEmails} variant="outline">
          Try Again
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          Emails from {domain}
        </h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">{emails.length} emails</span>
          <Button onClick={loadEmails} variant="ghost" size="sm">
            Refresh
          </Button>
        </div>
      </div>
      
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {emails.map((email, index) => (
          <Card
            key={`${email.sender}-${email.subject}-${index}`}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedEmail?.subject === email.subject && selectedEmail?.sender === email.sender
                ? 'ring-2 ring-primary-500 bg-primary-50' 
                : 'hover:bg-gray-50'
            }`}
            padding="sm"
            onClick={() => onEmailSelect(email)}
          >
            <div className="space-y-2">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">
                    {email.subject}
                  </h3>
                  <p className="text-sm text-gray-600">
                    From: {email.sender}
                  </p>
                </div>
                <div className="flex items-center space-x-2 ml-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(email.priority)}`}>
                    {email.priority.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-500 whitespace-nowrap">
                    {formatDate(email.received_date)}
                  </span>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 line-clamp-2">
                {truncateText(email.body, 150)}
              </p>
            </div>
          </Card>
        ))}
      </div>
      
      {emails.length === 0 && (
        <Card className="text-center py-8">
          <p className="text-gray-600">No emails found in {domain}</p>
        </Card>
      )}
    </div>
  );
};

export default EmailList; 