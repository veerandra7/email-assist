"""
Gmail service for OAuth2 authentication and email operations.
Follows Single Responsibility Principle - handles only Gmail operations.
"""
import os
import json
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models.email_models import EmailContent, EmailDomain, DomainAnalysis, EmailPriority
from app.core.config import get_settings
from app.core.exceptions import EmailProcessingException, InvalidEmailDomainException

logger = logging.getLogger(__name__)


class GmailService:
    """
    Gmail service for OAuth2 authentication and email operations.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize Gmail service."""
        self.session_id = session_id
        if session_id:
            self.credentials_file = f"gmail_credentials_{session_id}.json"
            self.token_file = f"gmail_token_{session_id}.json"
        else:
            # Fallback to global files for backward compatibility
            self.credentials_file = "gmail_credentials.json"
            self.token_file = "gmail_token.json"
        
        self.service = None
        self.settings = get_settings()
        
        # Load existing credentials if available
        self._load_existing_credentials()
    
    def _load_existing_credentials(self):
        """Load existing credentials if available."""
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.settings.gmail_scopes)
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
    
    def _create_credentials_file(self):
        """Create Gmail OAuth2 credentials file."""
        if not self.settings.gmail_client_id or not self.settings.gmail_client_secret:
            raise EmailProcessingException("Gmail OAuth2 credentials not configured")
        
        credentials = {
            "web": {
                "client_id": self.settings.gmail_client_id,
                "client_secret": self.settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.settings.gmail_redirect_uri]
            }
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to file."""
        with open(self.token_file, 'w') as f:
            f.write(creds.to_json())
    
    def get_auth_url(self) -> str:
        """Get Gmail OAuth2 authorization URL."""
        if not self.settings.gmail_client_id or not self.settings.gmail_client_secret:
            raise EmailProcessingException("Gmail OAuth2 credentials not configured")
        
        # Create credentials file if not exists
        if not os.path.exists(self.credentials_file):
            self._create_credentials_file()
        
        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=self.settings.gmail_scopes,
            redirect_uri=self.settings.gmail_redirect_uri
        )
        
        # Include session ID in state parameter to link callback to correct session
        state_data = self.session_id if self.session_id else "no_session"
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # Force consent screen to get refresh token
            login_hint=None,
            state=state_data  # Pass session ID in state parameter
        )
        
        return auth_url
    
    def authenticate_with_code(self, auth_code: str) -> bool:
        """Authenticate with authorization code and save credentials."""
        try:
            if not os.path.exists(self.credentials_file):
                self._create_credentials_file()
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.settings.gmail_scopes,
                redirect_uri=self.settings.gmail_redirect_uri
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
        """Fetch emails from Gmail with performance optimizations."""
        if not self.is_authenticated():
            raise EmailProcessingException("Not authenticated with Gmail")
        
        try:
            # Limit max results for performance (Gmail API is slow with large requests)
            safe_max_results = min(max_results, 50)
            
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=safe_max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            # Process only limited messages for better performance
            for message in messages[:safe_max_results]:
                try:
                    # Get message with minimal format for faster processing
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'  # We need full format for body extraction
                    ).execute()
                    
                    # Extract email data
                    headers = msg['payload'].get('headers', [])
                    email_data = {}
                    
                    for header in headers:
                        name = header['name'].lower()
                        if name in ['subject', 'from', 'to', 'date']:
                            email_data[name] = header['value']
                    
                    # Extract body
                    body = self._extract_body(msg['payload'])
                    
                    if email_data.get('from') and email_data.get('subject'):
                        # Parse date
                        date_str = email_data.get('date', '')
                        try:
                            from email.utils import parsedate_to_datetime
                            received_date = parsedate_to_datetime(date_str)
                            # Ensure timezone awareness
                            if received_date.tzinfo is None:
                                received_date = received_date.replace(tzinfo=timezone.utc)
                        except:
                            received_date = datetime.now(timezone.utc)
                        
                        # Extract domain from sender
                        sender_email = email_data['from']
                        domain = sender_email.split('@')[-1] if '@' in sender_email else 'unknown'
                        
                        email_content = EmailContent(
                            subject=email_data['subject'],
                            body=body,
                            sender=email_data['from'],
                            recipient=email_data.get('to', ''),
                            received_date=received_date,
                            domain=domain,
                            message_id=message['id']
                        )
                        
                        emails.append(email_content)
                        
                except Exception as e:
                    print(f"Error processing message {message['id']}: {e}")
                    continue
            
            return emails
            
        except HttpError as e:
            raise EmailProcessingException(f"Failed to fetch emails: {str(e)}")
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body.strip()
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via Gmail."""
        if not self.is_authenticated():
            raise EmailProcessingException("Not authenticated with Gmail")
        
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return True
            
        except HttpError as e:
            raise EmailProcessingException(f"Failed to send email: {str(e)}")
    
    def send_reply(self, original_email: EmailContent, reply_body: str) -> bool:
        """Send a reply to an email via Gmail."""
        if not self.is_authenticated():
            raise EmailProcessingException("Not authenticated with Gmail")
        
        try:
            # Create reply message
            message = MIMEText(reply_body)
            message['to'] = original_email.sender
            
            # Create reply subject (add "Re: " if not already present)
            original_subject = original_email.subject
            if not original_subject.lower().startswith('re:'):
                reply_subject = f"Re: {original_subject}"
            else:
                reply_subject = original_subject
            
            message['subject'] = reply_subject
            
            # Set In-Reply-To and References headers for proper threading
            # Note: In a full implementation, we'd need the original message ID
            # For now, we'll send as a regular email to the sender
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return True
            
        except HttpError as e:
            raise EmailProcessingException(f"Failed to send reply: {str(e)}")
    
    def get_domains(self, emails: List[EmailContent]) -> List[EmailDomain]:
        """Analyze email domains and return domain statistics."""
        domain_stats = {}
        
        def normalize_datetime(dt):
            """Ensure datetime is timezone-aware."""
            if dt.tzinfo is None:
                # If naive, assume UTC
                return dt.replace(tzinfo=timezone.utc)
            return dt
        
        for email in emails:
            domain = email.domain
            normalized_date = normalize_datetime(email.received_date)
            
            if domain not in domain_stats:
                domain_stats[domain] = {
                    'count': 0,
                    'last_received': normalized_date,
                    'importance_score': 0.5  # Default importance
                }
            
            domain_stats[domain]['count'] += 1
            if normalized_date > domain_stats[domain]['last_received']:
                domain_stats[domain]['last_received'] = normalized_date
        
        # Calculate importance scores based on frequency and recency
        total_emails = len(emails)
        current_time = datetime.now(timezone.utc)
        
        for domain, stats in domain_stats.items():
            frequency_score = stats['count'] / total_emails
            recency_score = 1.0 if stats['last_received'] > current_time - timedelta(days=7) else 0.5
            stats['importance_score'] = (frequency_score * 0.7) + (recency_score * 0.3)
        
        return [
            EmailDomain(
                domain=domain,
                count=stats['count'],
                importance_score=stats['importance_score'],
                last_received=stats['last_received']
            )
            for domain, stats in domain_stats.items()
        ]
    
    def get_emails_by_domain(self, domain: str, limit: int = 20) -> List[EmailContent]:
        """Get emails from a specific domain using Gmail search."""
        if not self.is_authenticated():
            raise EmailProcessingException("Gmail authentication required. Please authenticate first.")
        
        try:
            # Use Gmail search query to filter by domain - much faster!
            search_query = f"from:{domain}"
            
            # Get list of messages matching domain
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=min(limit, 50)  # Limit to prevent slowness
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            # Process only the first few messages for speed
            for message in messages[:limit]:
                try:
                    # Get minimal message details for faster processing
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='metadata',  # Only get headers, not full body for speed
                        metadataHeaders=['subject', 'from', 'to', 'date']
                    ).execute()
                    
                    # Extract email data from metadata
                    headers = msg['payload'].get('headers', [])
                    email_data = {}
                    
                    for header in headers:
                        name = header['name'].lower()
                        if name in ['subject', 'from', 'to', 'date']:
                            email_data[name] = header['value']
                    
                    if email_data.get('from') and email_data.get('subject'):
                        # Parse date
                        date_str = email_data.get('date', '')
                        try:
                            from email.utils import parsedate_to_datetime
                            received_date = parsedate_to_datetime(date_str)
                            # Ensure timezone awareness
                            if received_date.tzinfo is None:
                                received_date = received_date.replace(tzinfo=timezone.utc)
                        except:
                            received_date = datetime.now(timezone.utc)
                        
                        # Extract domain from sender
                        sender_email = email_data['from']
                        email_domain = sender_email.split('@')[-1] if '@' in sender_email else 'unknown'
                        if '<' in sender_email and '>' in sender_email:
                            email_address_part = sender_email.split('<')[1].split('>')[0]
                            email_domain = email_address_part.split('@')[-1] if '@' in email_address_part else 'unknown'
                        
                        email_content = EmailContent(
                            subject=email_data['subject'],
                            body="",  # Empty body for list view - will be loaded on demand
                            sender=email_data['from'],
                            recipient=email_data.get('to', ''),
                            received_date=received_date,
                            domain=email_domain,
                            message_id=message['id']  # Store Gmail message ID for on-demand loading
                        )
                        
                        emails.append(email_content)
                        
                except Exception as e:
                    print(f"Error processing message {message['id']}: {e}")
                    continue
            
            return emails
            
        except Exception as e:
            raise EmailProcessingException(f"Failed to get emails for domain {domain}: {str(e)}")
    
    def get_email_by_id(self, message_id: str) -> EmailContent:
        """Get a single email by message ID with full body content."""
        if not self.is_authenticated():
            raise EmailProcessingException("Gmail authentication required. Please authenticate first.")
        
        try:
            # Get full message details
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract email data
            headers = msg['payload'].get('headers', [])
            email_data = {}
            
            for header in headers:
                name = header['name'].lower()
                if name in ['subject', 'from', 'to', 'date']:
                    email_data[name] = header['value']
            
            # Extract full body
            body = self._extract_body(msg['payload'])
            
            if email_data.get('from') and email_data.get('subject'):
                # Parse date
                date_str = email_data.get('date', '')
                try:
                    from email.utils import parsedate_to_datetime
                    received_date = parsedate_to_datetime(date_str)
                    if received_date.tzinfo is None:
                        received_date = received_date.replace(tzinfo=timezone.utc)
                except:
                    received_date = datetime.now(timezone.utc)
                
                # Extract domain from sender
                sender_email = email_data['from']
                domain = sender_email.split('@')[-1] if '@' in sender_email else 'unknown'
                if '<' in sender_email and '>' in sender_email:
                    email_address_part = sender_email.split('<')[1].split('>')[0]
                    domain = email_address_part.split('@')[-1] if '@' in email_address_part else 'unknown'
                
                return EmailContent(
                    subject=email_data['subject'],
                    body=body,
                    sender=email_data['from'],
                    recipient=email_data.get('to', ''),
                    received_date=received_date,
                    domain=domain,
                    message_id=message_id
                )
            
            raise EmailProcessingException("Email missing required fields")
            
        except Exception as e:
            raise EmailProcessingException(f"Failed to get email {message_id}: {str(e)}")
    
    def get_all_domains(self) -> List[EmailDomain]:
        """Get email domains using representative sampling for accurate counts."""
        if not self.is_authenticated():
            raise EmailProcessingException("Gmail authentication required. Please authenticate first.")
        
        try:
            logger.info("📊 Getting domains using representative sampling...")
            
            # Get a balanced sample for domain representation 
            # 100 emails should give us good domain coverage without being too slow
            sample_emails = self.get_emails(max_results=100)
            
            # Group emails by domain and count them
            domain_stats = {}
            for email in sample_emails:
                domain = email.domain
                if domain not in domain_stats:
                    domain_stats[domain] = {
                        'count': 0,
                        'last_received': email.received_date,
                        'emails': []
                    }
                
                domain_stats[domain]['count'] += 1
                domain_stats[domain]['emails'].append(email)
                
                # Update last received date
                if email.received_date > domain_stats[domain]['last_received']:
                    domain_stats[domain]['last_received'] = email.received_date
            
            logger.info(f"📊 Found {len(domain_stats)} domains from sample of {len(sample_emails)} emails")
            
            domains_with_counts = []
            total_sample = len(sample_emails)
            
            # Process each domain
            for domain, stats in domain_stats.items():
                try:
                    actual_count = stats['count']  # Use sample count (more reliable)
                    last_received = stats['last_received']
                    
                    # Calculate importance score based on frequency and recency
                    frequency_score = stats['count'] / total_sample
                    
                    current_time = datetime.now(timezone.utc)
                    days_ago = (current_time - last_received).days
                    
                    # Recency scoring: recent = high score
                    if days_ago <= 1:
                        recency_score = 1.0
                    elif days_ago <= 7:
                        recency_score = 0.8
                    elif days_ago <= 30:
                        recency_score = 0.5
                    else:
                        recency_score = 0.2
                    
                    importance_score = (frequency_score * 0.6) + (recency_score * 0.4)
                    
                    domains_with_counts.append(EmailDomain(
                        domain=domain,
                        count=actual_count,
                        importance_score=min(importance_score, 1.0),  # Cap at 1.0
                        last_received=last_received
                    ))
                    
                    logger.debug(f"📊 Domain {domain}: {actual_count} emails, score={importance_score:.3f}")
                    
                except Exception as e:
                    logger.warning(f"Error processing domain {domain}: {e}")
                    # Use basic data as fallback
                    domains_with_counts.append(EmailDomain(
                        domain=domain,
                        count=stats['count'],
                        importance_score=0.3,
                        last_received=stats['last_received']
                    ))
            
            # Sort by importance score, then by count (most important first)
            domains_with_counts.sort(key=lambda d: (d.importance_score, d.count), reverse=True)
            
            logger.info(f"✅ Returning {len(domains_with_counts)} domains with sample-based counts")
            return domains_with_counts
            
        except Exception as e:
            logger.error(f"❌ Failed to get domains: {str(e)}")
            raise EmailProcessingException(f"Failed to get email domains: {str(e)}")
    
    def logout(self):
        """Logout and clear all stored credentials."""
        self._clear_sessions()
        self.service = None
        print("✅ Gmail service logged out and sessions cleared")
    
    def _clear_sessions(self):
        """Clear all stored credentials and sessions."""
        try:
            files_to_remove = [self.credentials_file, self.token_file]
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️ Cleared session file: {file_path}")
            print("✅ All Gmail sessions cleared - fresh authentication required")
        except Exception as e:
            print(f"⚠️ Warning: Could not clear some session files: {e}")
