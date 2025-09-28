/**
 * Domain list component - displays email domains with importance scores
 */
import React, { useState, useEffect } from 'react';
import { EmailDomain } from '../types/email';
import { emailAPI, handleAPIError } from '../utils/api';
import Button from './ui/Button';
import Card from './ui/Card';
import LoadingSpinner from './ui/LoadingSpinner';

interface DomainListProps {
  onDomainSelect: (domain: string) => void;
  selectedDomain?: string;
}

const DomainList: React.FC<DomainListProps> = ({ onDomainSelect, selectedDomain }) => {
  const [domains, setDomains] = useState<EmailDomain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDomains();
  }, []);

  const loadDomains = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await emailAPI.getDomains();
      setDomains(data);
    } catch (err) {
      setError(handleAPIError(err));
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (score: number) => {
    if (score >= 0.8) return 'text-red-600 bg-red-50';
    if (score >= 0.6) return 'text-orange-600 bg-orange-50';
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getPriorityLabel = (score: number) => {
    if (score >= 0.8) return 'Urgent';
    if (score >= 0.6) return 'High';
    if (score >= 0.4) return 'Medium';
    return 'Low';
  };

  if (loading) {
    return (
      <Card className="text-center py-8">
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <p className="text-gray-600">Loading email domains...</p>
        <p className="text-sm text-gray-500 mt-2">Gmail API can be slow, please wait...</p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="text-center py-8">
        <div className="text-red-600 mb-4">
          <p className="font-medium">Failed to load domains</p>
          <p className="text-sm">{error}</p>
        </div>
        <Button onClick={loadDomains} variant="outline">
          Try Again
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Email Domains</h2>
        <Button onClick={loadDomains} variant="ghost" size="sm">
          Refresh
        </Button>
      </div>
      
      <div className="grid gap-3">
        {domains.map((domain) => (
          <Card
            key={domain.domain}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedDomain === domain.domain 
                ? 'ring-2 ring-primary-500 bg-primary-50' 
                : 'hover:bg-gray-50'
            }`}
            padding="sm"
            onClick={() => onDomainSelect(domain.domain)}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <h3 className="font-medium text-gray-900">{domain.domain}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(domain.importance_score)}`}>
                    {getPriorityLabel(domain.importance_score)}
                  </span>
                </div>
                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                  <span>{domain.count} emails</span>
                  <span>Score: {(domain.importance_score * 100).toFixed(0)}%</span>
                  {domain.last_received && (
                    <span>
                      Last: {new Date(domain.last_received).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center">
                <div className="w-16 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all"
                    style={{ width: `${domain.importance_score * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
      
      {domains.length === 0 && (
        <Card className="text-center py-8">
          <p className="text-gray-600">No email domains found</p>
        </Card>
      )}
    </div>
  );
};

export default DomainList; 