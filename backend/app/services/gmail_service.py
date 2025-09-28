"""
Gmail service for OAuth2 authentication and email operations.
Follows Single Responsibility Principle - handles only Gmail operations.
"""
import os
import json
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models.email_models import EmailContent, EmailDomain, DomainAnalysis, EmailPriority
from app.core.config import settings
from app.core.exceptions import EmailProcessingException, InvalidEmailDomainException


class GmailService:
    """Gmail service for authentication and email operations."""
    
    def __init__(self):
        """Initialize Gmail service."""
        self.credentials_file = "gmail_credentials.json"
        self.token_file = "gmail_token.json"
        self.service = None
        self._load_existing_credentials()
    
    def _load_existing_credentials(self):
        """Load existing credentials if available."""
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, settings.gmail_scopes)
                if creds and creds.valid:
                    self.service = build('gmail', 'v1', credentials=creds)
                elif creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.service = build('gmail', 'v1', credentials=creds)
                    self._save_credentials(creds)
                else:
                    print(f"Invalid credentials: missing refresh_token or invalid state")
                    # Delete invalid token file to force re-authentication
                    os.remove(self.token_file)
            except Exception as e:
                print(f"Error loading existing credentials: {e}")
                # Clean up corrupted token file
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
    
    def get_auth_url(self) -> str:
        """Get Gmail OAuth2 authorization URL."""
        if not settings.gmail_client_id or not settings.gmail_client_secret:
            raise EmailProcessingException("Gmail OAuth2 credentials not configured")
        
        # Create credentials file if not exists
        if not os.path.exists(self.credentials_file):
            self._create_credentials_file()
        
        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=settings.gmail_scopes,
            redirect_uri=settings.gmail_redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # Force consent screen to get refresh token
                            login_hint=None
        )
        
        return auth_url
    
    def authenticate_with_code(self, auth_code: str) -> bool:
        """Authenticate with authorization code and save credentials."""
        try:
            if not os.path.exists(self.credentials_file):
                self._create_credentials_file()
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=settings.gmail_scopes,
                redirect_uri=settings.gmail_redirect_uri
            )
            
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save credentials
            self._save_credentials(creds)
            
            # Initialize service
            self.service = build('gmail', 'v1', credentials=creds)
            
            return True
            
        except Exception as e:
            raise EmailProcessingException(f"Failed to authenticate: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if Gmail service is authenticated."""
        return self.service is not None
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        if not self.is_authenticated():
            raise EmailProcessingException("Not authenticated with Gmail")
        
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                "email": profile.get('emailAddress'),
                "messages_total": profile.get('messagesTotal', 0),
                "threads_total": profile.get('threadsTotal', 0)
            }
        except HttpError as e:
            raise EmailProcessingException(f"Failed to get user profile: {str(e)}")
    
    def get_emails(self, max_results: int = 100) -> List[EmailContent]:
        """Fetch emails from Gmail."""
        if not self.is_authenticated():
            raise EmailProcessingException("Not authenticated with Gmail")
        
        try:
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q='in:inbox'  # Only inbox emails
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self._get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except HttpError as e:
            raise EmailProcessingException(f"Failed to fetch emails: {str(e)}")
    
    def get_emails_by_domain(self, domain: str, limit: int = 20) -> List[EmailContent]:
        """Get emails from a specific domain."""
        if not self.is_authenticated():
            raise EmailProcessingException("Not authenticated with Gmail")
        
        try:
            # Search for emails from specific domain
            query = f'from:{domain} in:inbox'
            results = self.service.users().messages().list(
                userId='me',
                maxResults=limit,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self._get_email_details_full(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except HttpError as e:
            raise EmailProcessingException(f"Failed to fetch emails from {domain}: {str(e)}")
    
    def get_all_domains(self) -> List[EmailDomain]:
        """Get all email domains with their statistics."""
        emails = self.get_emails(50)  # Reduced from 500 to 50 for better performance
        return self._analyze_domains(emails)
    
    def send_reply(self, original_email: EmailContent, reply_body: str) -> bool:
        """Send a reply to an email."""
        if not self.is_authenticated():
            raise EmailProcessingException("Not authenticated with Gmail")
        
        try:
            # Create reply message
            message = MIMEMultipart()
            message['to'] = original_email.sender
            message['subject'] = f"Re: {original_email.subject}"
            
            # Add reply body
            message.attach(MIMEText(reply_body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return True
            
        except HttpError as e:
            raise EmailProcessingException(f"Failed to send reply: {str(e)}")
    
    def _get_email_details(self, message_id: str) -> Optional[EmailContent]:
        """Get detailed information for a specific email."""
        try:
            # Use 'metadata' format for faster processing when we only need headers
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='metadata',
                metadataHeaders=['Subject', 'From', 'To', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
            
            # Parse date
            date_str = headers.get('Date', '')
            received_date = self._parse_date(date_str)
            
            # Extract domain from sender
            sender = headers.get('From', '')
            domain = self._extract_domain(sender)
            
            # Use simplified priority determination without body
            priority = self._determine_priority_simple(headers)
            
            return EmailContent(
                subject=headers.get('Subject', 'No Subject'),
                body="",  # Don't fetch body for domain analysis to improve performance
                sender=sender,
                recipient=headers.get('To', ''),
                received_date=received_date,
                priority=priority,
                domain=domain
            )
            
        except Exception as e:
            print(f"Error processing email {message_id}: {e}")
            return None
    
    def _get_email_details_full(self, message_id: str) -> Optional[EmailContent]:
        """Get full detailed information for a specific email including body."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
            
            # Extract email body
            body = self._extract_body(message['payload'])
            
            # Parse date
            date_str = headers.get('Date', '')
            received_date = self._parse_date(date_str)
            
            # Extract domain from sender
            sender = headers.get('From', '')
            domain = self._extract_domain(sender)
            
            # Determine priority with full body analysis
            priority = self._determine_priority(headers, body)
            
            return EmailContent(
                subject=headers.get('Subject', 'No Subject'),
                body=body[:settings.max_email_length],  # Limit body length
                sender=sender,
                recipient=headers.get('To', ''),
                received_date=received_date,
                priority=priority,
                domain=domain
            )
            
        except Exception as e:
            print(f"Error processing email {message_id}: {e}")
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
        elif payload['mimeType'] == 'text/plain':
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string."""
        try:
            # Gmail date format: "Wed, 21 Sep 2025 10:30:00 +0000"
            from email.utils import parsedate_to_datetime
            import pytz
            parsed_date = parsedate_to_datetime(date_str)
            # Ensure timezone awareness
            if parsed_date.tzinfo is None:
                parsed_date = pytz.UTC.localize(parsed_date)
            return parsed_date
        except:
            import pytz
            return datetime.now(pytz.UTC)
    
    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address."""
        try:
            from email.utils import parseaddr
            _, email_addr = parseaddr(email)
            if '@' in email_addr:
                return email_addr.split('@')[1].lower()
            return 'unknown'
        except:
            return 'unknown'
    
    def _determine_priority(self, headers: Dict, body: str) -> EmailPriority:
        """Determine email priority based on headers and content."""
        # Check for explicit priority headers
        priority_header = headers.get('X-Priority', '').lower()
        importance = headers.get('Importance', '').lower()
        
        if priority_header in ['1', '2'] or importance == 'high':
            return EmailPriority.HIGH
        elif 'urgent' in headers.get('Subject', '').lower():
            return EmailPriority.URGENT
        elif any(word in body.lower() for word in ['urgent', 'asap', 'immediately', 'critical']):
            return EmailPriority.HIGH
        elif any(word in body.lower() for word in ['newsletter', 'unsubscribe', 'promotion']):
            return EmailPriority.LOW
        else:
            return EmailPriority.MEDIUM
    
    def _determine_priority_simple(self, headers: Dict) -> EmailPriority:
        """Determine email priority based on headers only (faster)."""
        # Check for explicit priority headers
        priority_header = headers.get('X-Priority', '').lower()
        importance = headers.get('Importance', '').lower()
        
        if priority_header in ['1', '2'] or importance == 'high':
            return EmailPriority.HIGH
        elif 'urgent' in headers.get('Subject', '').lower():
            return EmailPriority.URGENT
        elif any(word in headers.get('Subject', '').lower() for word in ['newsletter', 'unsubscribe', 'promotion']):
            return EmailPriority.LOW
        else:
            return EmailPriority.MEDIUM
    
    def _analyze_domains(self, emails: List[EmailContent]) -> List[EmailDomain]:
        """Analyze email domains and calculate importance scores."""
        domain_stats: Dict[str, Dict[str, Any]] = {}
        
        for email in emails:
            domain = email.domain
            
            if domain not in domain_stats:
                domain_stats[domain] = {
                    'count': 0,
                    'last_received': email.received_date,
                    'priority_sum': 0
                }
            
            domain_stats[domain]['count'] += 1
            domain_stats[domain]['priority_sum'] += self._get_priority_weight(email.priority)
            
            if email.received_date > domain_stats[domain]['last_received']:
                domain_stats[domain]['last_received'] = email.received_date
        
        # Calculate importance scores
        total_emails = len(emails)
        domains = []
        
        for domain, stats in domain_stats.items():
            # Importance based on frequency, recency, and priority
            frequency_score = stats['count'] / total_emails if total_emails > 0 else 0
            avg_priority = stats['priority_sum'] / stats['count'] if stats['count'] > 0 else 0
            
            # Recency score (higher for more recent emails)
            import pytz
            now = datetime.now(pytz.UTC)
            last_received = stats['last_received']
            if last_received.tzinfo is None:
                last_received = pytz.UTC.localize(last_received)
            days_since_last = (now - last_received).days
            recency_score = max(0, 1 - (days_since_last / 30))  # Decay over 30 days
            
            importance_score = min(1.0, (frequency_score * 0.4 + 
                                        avg_priority * 0.4 + 
                                        recency_score * 0.2))
            
            domains.append(EmailDomain(
                domain=domain,
                count=stats['count'],
                importance_score=round(importance_score, 3),
                last_received=stats['last_received']
            ))
        
        # Sort by importance score descending
        domains.sort(key=lambda x: x.importance_score, reverse=True)
        return domains
    
    def _get_priority_weight(self, priority: EmailPriority) -> float:
        """Convert priority enum to numeric weight."""
        weights = {
            EmailPriority.LOW: 0.25,
            EmailPriority.MEDIUM: 0.5,
            EmailPriority.HIGH: 0.75,
            EmailPriority.URGENT: 1.0
        }
        return weights.get(priority, 0.5)
    
    def _create_credentials_file(self):
        """Create credentials file from environment variables."""
        credentials = {
            "web": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [settings.gmail_redirect_uri]
            }
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f)
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to file."""
        with open(self.token_file, 'w') as token:
            token.write(creds.to_json()) 