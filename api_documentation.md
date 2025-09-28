# API Documentation - Email AI Assistant

## 🔗 Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## 📋 API Overview

The Email AI Assistant provides RESTful APIs for email management, AI-powered summarization, and response generation. All endpoints follow standard HTTP methods and return JSON responses.

### Response Format
All API responses follow this standard format:
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Error Handling
Error responses include detailed information:
```json
{
  "detail": "Error description",
  "type": "ErrorType",
  "status_code": 400
}
```

## 🔐 Authentication

### Gmail OAuth2 Flow

#### 1. Initiate OAuth
```http
GET /auth/gmail/login
```

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random_state_string"
}
```

#### 2. OAuth Callback
```http
GET /auth/gmail/callback?code={auth_code}&state={state}
```

**Response:**
```json
{
  "status": "success",
  "message": "Authentication successful",
  "user_info": {
    "email": "user@gmail.com",
    "name": "User Name"
  }
}
```

#### 3. Check Authentication Status
```http
GET /auth/gmail/status
```

**Response:**
```json
{
  "authenticated": true,
  "user_email": "user@gmail.com",
  "expires_at": "2024-01-01T12:00:00.000Z"
}
```

#### 4. Logout
```http
POST /auth/gmail/logout
```

**Response:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

## 📧 Email Endpoints

### Get Email Domains

Retrieve all email domains with importance scores.

```http
GET /api/emails/domains
```

**Query Parameters:**
- `limit` (integer, optional): Maximum number of domains to return (default: 50)
- `min_importance` (float, optional): Minimum importance score filter (0.0-1.0)

**Response:**
```json
[
  {
    "domain": "example.com",
    "count": 25,
    "importance_score": 0.85,
    "last_email_date": "2024-01-01T12:00:00.000Z",
    "avg_body_length": 1250
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/emails/domains?limit=10&min_importance=0.7"
```

### Get Emails by Domain

Retrieve emails from a specific domain.

```http
GET /api/emails/domains/{domain}/emails
```

**Path Parameters:**
- `domain` (string): Email domain (e.g., "example.com")

**Query Parameters:**
- `limit` (integer, optional): Number of emails to return (default: 20, max: 100)
- `offset` (integer, optional): Number of emails to skip (default: 0)

**Response:**
```json
[
  {
    "id": "email_id_123",
    "subject": "Meeting Tomorrow",
    "sender": "john@example.com",
    "sender_name": "John Doe",
    "body": "Email content...",
    "received_date": "2024-01-01T12:00:00.000Z",
    "thread_id": "thread_123",
    "labels": ["INBOX", "IMPORTANT"],
    "has_attachments": false,
    "body_length": 150
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/emails/domains/example.com/emails?limit=5"
```

### Summarize Email

Generate AI-powered summary for an email.

```http
POST /api/emails/summarize
```

**Request Body:**
```json
{
  "id": "email_id_123",
  "subject": "Meeting Tomorrow",
  "sender": "john@example.com",
  "sender_name": "John Doe",
  "body": "Hi there, I wanted to confirm our meeting tomorrow at 2 PM...",
  "received_date": "2024-01-01T12:00:00.000Z"
}
```

**Response:**
```json
{
  "summary": "John is confirming a meeting scheduled for tomorrow at 2 PM and asking for agenda items.",
  "key_points": [
    "Meeting confirmation for tomorrow 2 PM",
    "Request for agenda items",
    "Location: Conference Room A"
  ],
  "action_required": true,
  "urgency_level": "medium",
  "priority": "normal",
  "confidence_score": 0.92,
  "processing_time_ms": 1250
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/emails/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "123",
    "subject": "Test Email",
    "sender": "test@example.com",
    "body": "This is a test email content."
  }'
```

### Generate Email Response

Create AI-powered email response.

```http
POST /api/emails/generate-response
```

**Request Body:**
```json
{
  "original_email": {
    "id": "email_id_123",
    "subject": "Meeting Tomorrow",
    "sender": "john@example.com",
    "sender_name": "John Doe",
    "body": "Email content...",
    "received_date": "2024-01-01T12:00:00.000Z"
  },
  "user_input": "Confirm the meeting and ask about the agenda",
  "tone": "professional"
}
```

**Available Tones:**
- `professional` - Business-appropriate, formal tone
- `friendly` - Warm, approachable tone
- `formal` - Very formal, traditional business tone
- `urgent` - Conveys urgency and importance
- `apologetic` - Acknowledges mistakes, expresses regret

**Response:**
```json
{
  "generated_response": "Hi John,\n\nThank you for confirming our meeting tomorrow at 2 PM. I'll be there in Conference Room A.\n\nCould you please share the agenda items you'd like to discuss? This will help me prepare accordingly.\n\nBest regards,\n[Your name]",
  "subject_suggestion": "Re: Meeting Tomorrow",
  "confidence_score": 0.89,
  "tone_used": "professional",
  "processing_time_ms": 2100,
  "word_count": 45
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/emails/generate-response" \
  -H "Content-Type: application/json" \
  -d '{
    "original_email": {
      "subject": "Project Update",
      "sender": "manager@company.com",
      "body": "Can you provide an update on the project status?"
    },
    "user_input": "Provide brief status update",
    "tone": "professional"
  }'
```

### Email Service Health Check

Check the health of the email service.

```http
GET /api/emails/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "service": "email-ai-backend",
  "version": "1.0.0",
  "gmail_connection": "connected",
  "last_sync": "2024-01-01T11:55:00.000Z"
}
```

## 🤖 AI Endpoints

### Get AI Provider Information

Get current AI provider details.

```http
GET /api/ai/provider
```

**Response:**
```json
{
  "provider": "Claude",
  "model": "claude-sonnet-4-20250514",
  "status": "active",
  "version": "3.0",
  "capabilities": [
    "text_generation",
    "summarization",
    "analysis"
  ],
  "rate_limits": {
    "requests_per_minute": 60,
    "tokens_per_minute": 100000
  }
}
```

### AI Service Health Check

Check the health of the AI service.

```http
GET /api/ai/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "service": "claude-ai",
  "api_key_valid": true,
  "last_request": "2024-01-01T11:58:00.000Z",
  "response_time_ms": 850
}
```

## 📊 Data Models

### EmailContent Model
```typescript
interface EmailContent {
  id: string;
  subject: string;
  sender: string;
  sender_name?: string;
  body: string;
  received_date: string;
  thread_id?: string;
  labels?: string[];
  has_attachments?: boolean;
  body_length?: number;
}
```

### EmailSummary Model
```typescript
interface EmailSummary {
  summary: string;
  key_points: string[];
  action_required: boolean;
  urgency_level: "low" | "medium" | "high";
  priority: "low" | "normal" | "high";
  confidence_score: number;
  processing_time_ms: number;
}
```

### ResponseRequest Model
```typescript
interface ResponseRequest {
  original_email: EmailContent;
  user_input: string;
  tone: "professional" | "friendly" | "formal" | "urgent" | "apologetic";
}
```

### ResponseGeneration Model
```typescript
interface ResponseGeneration {
  generated_response: string;
  subject_suggestion: string;
  confidence_score: number;
  tone_used: string;
  processing_time_ms: number;
  word_count: number;
}
```

### EmailDomain Model
```typescript
interface EmailDomain {
  domain: string;
  count: number;
  importance_score: number;
  last_email_date: string;
  avg_body_length: number;
}
```

## 🚨 Error Codes

### HTTP Status Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | AI service or Gmail API unavailable |

### Custom Error Types

#### AIServiceException
```json
{
  "detail": "Failed to generate response: API key invalid",
  "type": "AIServiceException",
  "status_code": 503
}
```

#### GmailAuthException
```json
{
  "detail": "Gmail authentication required",
  "type": "GmailAuthException", 
  "status_code": 401
}
```

#### ValidationError
```json
{
  "detail": "Email body cannot be empty",
  "type": "ValidationError",
  "status_code": 422
}
```

## 📈 Rate Limits

### API Rate Limits
- **Email endpoints**: 100 requests per minute per user
- **AI endpoints**: 60 requests per minute per user
- **Authentication endpoints**: 10 requests per minute per IP

### Claude AI Limits
- Model-specific rate limits apply
- Monitor usage through response headers:
  ```
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 45
  X-RateLimit-Reset: 1640995200
  ```

## 🧪 Testing Examples

### Complete Workflow Test
```bash
# 1. Check health
curl http://localhost:8000/api/emails/health

# 2. Initiate OAuth (open returned URL in browser)
curl http://localhost:8000/auth/gmail/login

# 3. Get domains (after authentication)
curl http://localhost:8000/api/emails/domains

# 4. Get emails from domain
curl "http://localhost:8000/api/emails/domains/example.com/emails?limit=1"

# 5. Summarize email
curl -X POST "http://localhost:8000/api/emails/summarize" \
  -H "Content-Type: application/json" \
  -d '{...email_data...}'

# 6. Generate response
curl -X POST "http://localhost:8000/api/emails/generate-response" \
  -H "Content-Type: application/json" \
  -d '{...request_data...}'
```

### Postman Collection
Import the API documentation from `http://localhost:8000/docs` for a complete Postman collection with example requests.

## 📚 SDKs and Libraries

### JavaScript/TypeScript Client
```typescript
import { EmailAIClient } from './email-ai-client';

const client = new EmailAIClient('http://localhost:8000');

// Get domains
const domains = await client.emails.getDomains();

// Summarize email
const summary = await client.emails.summarize(emailData);

// Generate response
const response = await client.emails.generateResponse({
  original_email: emailData,
  user_input: "Acknowledge and ask for more details",
  tone: "professional"
});
```

### Python Client
```python
from email_ai_client import EmailAIClient

client = EmailAIClient("http://localhost:8000")

# Get domains
domains = client.emails.get_domains()

# Summarize email
summary = client.emails.summarize(email_data)

# Generate response
response = client.emails.generate_response(
    original_email=email_data,
    user_input="Acknowledge and ask for more details",
    tone="professional"
)
```

---

*For interactive API documentation, visit: `http://localhost:8000/docs`*
*For alternative documentation format, visit: `http://localhost:8000/redoc`* 