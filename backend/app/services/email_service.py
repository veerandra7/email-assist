"""
Email service for processing and managing emails.
Follows Single Responsibility Principle - handles only email operations.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from email.utils import parseaddr

from app.models.email_models import (
    EmailContent, EmailDomain, DomainAnalysis, EmailPriority
)
from app.core.exceptions import (
    EmailProcessingException, InvalidEmailDomainException
)
from app.services.gmail_service import GmailService

# Configure logger
logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for email processing and domain analysis.
    Follows Interface Segregation Principle - focused interface.
    """
    
    def __init__(self):
        """Initialize email service with Gmail integration."""
        logger.info("📧 Initializing Email Service...")
        try:
            self.gmail_service = GmailService()
            logger.info("✅ Email Service initialized successfully with Gmail integration")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Email Service: {str(e)}")
            raise
    
    def extract_domain_from_email(self, email: str) -> str:
        """
        Extract domain from email address.
        
        Args:
            email: Email address string
            
        Returns:
            Domain name
            
        Raises:
            InvalidEmailDomainException: If email format is invalid
        """
        logger.debug(f"🔍 Extracting domain from email: {email}")
        
        try:
            _, email_addr = parseaddr(email)
            logger.debug(f"📝 Parsed email address: {email_addr}")
            
            if '@' not in email_addr:
                logger.error(f"❌ Invalid email format - no @ symbol: {email}")
                raise InvalidEmailDomainException(f"Invalid email format: {email}")
            
            domain = email_addr.split('@')[1].lower()
            logger.debug(f"🌐 Extracted domain: {domain}")
            
            if not domain:
                logger.error(f"❌ Empty domain in email: {email}")
                raise InvalidEmailDomainException(f"Empty domain in email: {email}")
            
            logger.info(f"✅ Successfully extracted domain '{domain}' from email '{email}'")
            return domain
            
        except Exception as e:
            logger.error(f"❌ Failed to extract domain from {email}: {str(e)}")
            raise InvalidEmailDomainException(f"Failed to extract domain: {str(e)}")
    
    def analyze_email_domains(self, emails: List[EmailContent]) -> DomainAnalysis:
        """
        Analyze email domains and calculate importance scores.
        
        Args:
            emails: List of email content objects
            
        Returns:
            Domain analysis with importance scores
        """
        logger.info(f"📊 Starting domain analysis for {len(emails)} emails...")
        
        try:
            domain_stats: Dict[str, Dict[str, Any]] = {}
            
            for i, email in enumerate(emails):
                domain = email.domain
                logger.debug(f"📧 Processing email {i+1}/{len(emails)} from domain: {domain}")
                
                if domain not in domain_stats:
                    logger.debug(f"🆕 New domain discovered: {domain}")
                    domain_stats[domain] = {
                        'count': 0,
                        'last_received': email.received_date,
                        'priority_sum': 0
                    }
                
                domain_stats[domain]['count'] += 1
                domain_stats[domain]['priority_sum'] += self._get_priority_weight(email.priority)
                
                if email.received_date > domain_stats[domain]['last_received']:
                    domain_stats[domain]['last_received'] = email.received_date
            
            logger.info(f"📋 Found {len(domain_stats)} unique domains")
            
            # Calculate importance scores
            total_emails = len(emails)
            domains = []
            
            for domain, stats in domain_stats.items():
                logger.debug(f"📈 Calculating importance score for domain: {domain}")
                
                # Importance based on frequency, recency, and priority
                frequency_score = stats['count'] / total_emails
                avg_priority = stats['priority_sum'] / stats['count']
                
                # Recency score (higher for more recent emails)
                days_since_last = (datetime.now() - stats['last_received']).days
                recency_score = max(0, 1 - (days_since_last / 30))  # Decay over 30 days
                
                importance_score = min(1.0, (frequency_score * 0.4 + 
                                            avg_priority * 0.4 + 
                                            recency_score * 0.2))
                
                logger.debug(f"📊 Domain {domain}: count={stats['count']}, freq={frequency_score:.3f}, "
                           f"avg_priority={avg_priority:.3f}, recency={recency_score:.3f}, "
                           f"importance={importance_score:.3f}")
                
                domains.append(EmailDomain(
                    domain=domain,
                    count=stats['count'],
                    importance_score=round(importance_score, 3),
                    last_received=stats['last_received']
                ))
            
            # Sort by importance score descending
            domains.sort(key=lambda x: x.importance_score, reverse=True)
            logger.info(f"🏆 Top domain by importance: {domains[0].domain} (score: {domains[0].importance_score})")
            
            analysis = DomainAnalysis(
                domains=domains,
                total_emails=total_emails,
                analysis_date=datetime.now()
            )
            
            logger.info(f"✅ Domain analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze domains: {str(e)}", exc_info=True)
            raise EmailProcessingException(f"Failed to analyze domains: {str(e)}")
    
    def get_emails_by_domain(self, domain: str, limit: int = 20) -> List[EmailContent]:
        """
        Get recent emails from a specific domain.
        
        Args:
            domain: Domain name to filter by
            limit: Maximum number of emails to return
            
        Returns:
            List of emails from the domain
        """
        logger.info(f"📬 Retrieving emails from domain '{domain}' (limit: {limit})")
        
        try:
            if not self.gmail_service.is_authenticated():
                logger.error("❌ Gmail authentication required for email retrieval")
                raise EmailProcessingException("Gmail authentication required. Please authenticate first.")
            
            logger.debug("✅ Gmail authentication verified")
            emails = self.gmail_service.get_emails_by_domain(domain, limit)
            
            logger.info(f"✅ Retrieved {len(emails)} emails from domain '{domain}'")
            return emails
            
        except Exception as e:
            logger.error(f"❌ Failed to get emails for domain {domain}: {str(e)}")
            raise EmailProcessingException(f"Failed to get emails for domain {domain}: {str(e)}")
    
    def get_all_domains(self) -> List[EmailDomain]:
        """Get all available email domains with their statistics."""
        logger.info("📋 Retrieving all email domains...")
        
        try:
            if not self.gmail_service.is_authenticated():
                logger.error("❌ Gmail authentication required for domain retrieval")
                raise EmailProcessingException("Gmail authentication required. Please authenticate first.")
            
            logger.debug("✅ Gmail authentication verified")
            domains = self.gmail_service.get_all_domains()
            
            logger.info(f"✅ Retrieved {len(domains)} domains from Gmail service")
            return domains
            
        except Exception as e:
            logger.error(f"❌ Failed to get email domains: {str(e)}")
            raise EmailProcessingException(f"Failed to get email domains: {str(e)}")
    
    def get_email_by_id(self, message_id: str) -> EmailContent:
        """
        Get full email content by message ID.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Full email content with body
        """
        logger.info(f"📧 Retrieving full email content for message ID: {message_id}")
        
        try:
            if not self.gmail_service.is_authenticated():
                logger.error("❌ Gmail authentication required for email retrieval")
                raise EmailProcessingException("Gmail authentication required. Please authenticate first.")
            
            logger.debug("✅ Gmail authentication verified")
            email = self.gmail_service.get_email_by_id(message_id)
            
            logger.info(f"✅ Retrieved full email content for: {email.subject}")
            return email
            
        except Exception as e:
            logger.error(f"❌ Failed to get email {message_id}: {str(e)}")
            raise EmailProcessingException(f"Failed to get email {message_id}: {str(e)}")
    
    def send_reply(self, original_email: EmailContent, reply_body: str) -> bool:
        """
        Send a reply to an email using Gmail.
        
        Args:
            original_email: Original email to reply to
            reply_body: Reply message content
            
        Returns:
            True if sent successfully
        """
        logger.info(f"📤 Sending reply to email '{original_email.subject}' from {original_email.sender}")
        logger.debug(f"📝 Reply body length: {len(reply_body)} characters")
        
        try:
            if not self.gmail_service.is_authenticated():
                logger.error("❌ Gmail authentication required for sending replies")
                raise EmailProcessingException("Gmail authentication required. Please authenticate first.")
            
            logger.debug("✅ Gmail authentication verified")
            result = self.gmail_service.send_reply(original_email, reply_body)
            
            if result:
                logger.info("✅ Reply sent successfully")
            else:
                logger.warning("⚠️ Reply sending returned False - check implementation")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send reply: {str(e)}")
            raise EmailProcessingException(f"Failed to send reply: {str(e)}")
    
    def _get_priority_weight(self, priority: EmailPriority) -> float:
        """Get numeric weight for email priority."""
        weights = {
            EmailPriority.LOW: 0.25,
            EmailPriority.MEDIUM: 0.5,
            EmailPriority.HIGH: 0.75,
            EmailPriority.URGENT: 1.0
        }
        weight = weights.get(priority, 0.5)
        logger.debug(f"🎯 Priority {priority} mapped to weight {weight}")
        return weight 