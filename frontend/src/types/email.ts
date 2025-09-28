/**
 * TypeScript types for email-related data structures.
 * Follows the backend Pydantic models for consistency.
 */

export enum EmailPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export interface EmailDomain {
  domain: string;
  count: number;
  importance_score: number;
  last_received?: string;
}

export interface EmailContent {
  subject: string;
  body: string;
  sender: string;
  recipient: string;
  received_date: string;
  priority: EmailPriority;
  domain: string;
}

export interface EmailSummary {
  original_email: EmailContent;
  summary: string;
  key_points: string[];
  action_required: boolean;
  urgency_level: EmailPriority;
  suggested_response_tone: string;
}

export interface ResponseRequest {
  original_email: EmailContent;
  user_input: string;
  tone?: string;
}

export interface ResponseGeneration {
  original_email: EmailContent;
  user_input: string;
  generated_response: string;
  confidence_score: number;
}

export interface DomainAnalysis {
  domains: EmailDomain[];
  total_emails: number;
  analysis_date: string;
}

export interface AIProvider {
  provider: string;
  status: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  version?: string;
  provider?: string;
  capabilities?: string[];
} 