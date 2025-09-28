/**
 * Email viewer component with AI summarization and response generation
 */
import React, { useState, useEffect } from 'react';
import { EmailContent, EmailSummary, ResponseGeneration } from '../types/email';
import { emailAPI, handleAPIError } from '../utils/api';
import Button from './ui/Button';
import Card from './ui/Card';
import LoadingSpinner from './ui/LoadingSpinner';

interface EmailViewerProps {
  email: EmailContent;
}

const EmailViewer: React.FC<EmailViewerProps> = ({ email }) => {
  const [summary, setSummary] = useState<EmailSummary | null>(null);
  const [response, setResponse] = useState<ResponseGeneration | null>(null);
  const [userInput, setUserInput] = useState('');
  const [tone, setTone] = useState('professional');
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingResponse, setLoadingResponse] = useState(false);
  const [sendingReply, setSendingReply] = useState(false);
  const [replySuccess, setReplySuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSummary(null);
    setResponse(null);
    setReplySuccess(false);
    setError(null);
  }, [email]);

  const handleSummarize = async () => {
    try {
      setLoadingSummary(true);
      setError(null);
      const summaryData = await emailAPI.summarizeEmail(email);
      setSummary(summaryData);
      // Automatically set the suggested tone from the summary
      if (summaryData.suggested_response_tone) {
        setTone(summaryData.suggested_response_tone.toLowerCase());
      }
    } catch (err) {
      setError(handleAPIError(err));
    } finally {
      setLoadingSummary(false);
    }
  };
  const handleGenerateResponse = async () => {
    if (!userInput.trim()) {
      setError('Please enter your response instructions');
      return;
    }

    try {
      setLoadingResponse(true);
      setError(null);
      const responseData = await emailAPI.generateResponse({
        original_email: email,
        user_input: userInput,
        tone
      });
      setResponse(responseData);
    } catch (err) {
      setError(handleAPIError(err));
    } finally {
      setLoadingResponse(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const sendReply = async (replyBody: string) => {
    try {
      setSendingReply(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/api/emails/send-reply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          original_email: email,
          reply_body: replyBody
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send reply');
      }

      setReplySuccess(true);
      // Clear the response after successful send
      setTimeout(() => setReplySuccess(false), 5000);
      
    } catch (err: any) {
      setError(err.message || 'Failed to send reply');
    } finally {
      setSendingReply(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Email Header */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <h1 className="text-2xl font-bold text-gray-900">{email.subject}</h1>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              email.priority === 'urgent' ? 'text-red-600 bg-red-50' :
              email.priority === 'high' ? 'text-orange-600 bg-orange-50' :
              email.priority === 'medium' ? 'text-yellow-600 bg-yellow-50' :
              'text-green-600 bg-green-50'
            }`}>
              {email.priority.toUpperCase()}
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">From:</span>
              <p className="text-gray-900">{email.sender}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">To:</span>
              <p className="text-gray-900">{email.recipient}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Date:</span>
              <p className="text-gray-900">{formatDate(email.received_date)}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Domain:</span>
              <p className="text-gray-900">{email.domain}</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Email Content */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Email Content</h2>
        <div className="prose max-w-none">
          <p className="whitespace-pre-wrap text-gray-700">{email.body}</p>
        </div>
      </Card>

      {/* AI Summarization */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">AI Summary</h2>
          <Button 
            onClick={handleSummarize} 
            loading={loadingSummary}
            disabled={loadingSummary}
          >
            {summary ? 'Regenerate Summary' : 'Generate Summary'}
          </Button>
        </div>

        {summary && (
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Summary</h3>
              <p className="text-gray-700">{summary.summary}</p>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Key Points</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {summary.key_points.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Action Required:</span>
                <p className={`font-medium ${summary.action_required ? 'text-red-600' : 'text-green-600'}`}>
                  {summary.action_required ? 'Yes' : 'No'}
                </p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Urgency:</span>
                <p className="font-medium text-gray-900">{summary.urgency_level.toUpperCase()}</p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Suggested Tone:</span>
                <button
                  onClick={() => setTone(summary.suggested_response_tone.toLowerCase())}
                  className="ml-2 font-medium text-blue-600 hover:text-blue-800 underline capitalize"
                  title="Click to use this tone"
                >
                  {summary.suggested_response_tone}
                  {tone === summary.suggested_response_tone.toLowerCase() && (
                    <span className="ml-1 text-green-600">✓</span>
                  )}
                </button>
              </div>            </div>
          </div>
        )}
      </Card>

      {/* Response Generation */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Generate Response</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Response Instructions
            </label>
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Tell the AI what kind of response you want to send..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tone
              {summary && summary.suggested_response_tone && 
                tone === summary.suggested_response_tone.toLowerCase() && (
                <span className="ml-2 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                  🤖 AI Suggested
                </span>
              )}
            </label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="professional">Professional</option>
              <option value="friendly">Friendly</option>
              <option value="formal">Formal</option>
              <option value="urgent">Urgent</option>
              <option value="apologetic">Apologetic</option>
            </select>
          </div>
          <Button 
            onClick={handleGenerateResponse}
            loading={loadingResponse}
            disabled={!userInput.trim() || loadingResponse}
            className="w-full"
          >
            Generate Response
          </Button>
        </div>

        {response && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-gray-900">Generated Response</h3>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">
                  Confidence: {(response.confidence_score * 100).toFixed(0)}%
                </span>
                <Button 
                  onClick={() => copyToClipboard(response.generated_response)}
                  variant="outline"
                  size="sm"
                >
                  Copy
                </Button>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="whitespace-pre-wrap text-gray-700">{response.generated_response}</p>
            </div>
            
            <div className="flex items-center justify-end space-x-3 pt-4">
              <Button 
                onClick={() => sendReply(response.generated_response)}
                loading={sendingReply}
                disabled={sendingReply}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {sendingReply ? 'Sending...' : 'Send Reply'}
              </Button>
            </div>
            
            {replySuccess && (
              <div className="bg-green-50 border border-green-200 rounded-md p-3 mt-4">
                <div className="flex items-center">
                  <svg className="w-4 h-4 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-green-600 font-medium">Reply sent successfully!</p>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Error Display */}
      {error && (
        <Card>
          <div className="text-red-600">
            <h3 className="font-medium mb-2">Error</h3>
            <p className="text-sm">{error}</p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default EmailViewer; 