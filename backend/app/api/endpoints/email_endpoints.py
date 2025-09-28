"""
Email-related API endpoints.
Follows Single Responsibility Principle - handles only email API operations.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from app.models.email_models import (
    EmailDomain, EmailContent, EmailSummary, ResponseRequest, ResponseGeneration
)
from app.services.email_service import EmailService
from app.services.ai_service import AIService
from app.services.gmail_service import GmailService
from app.core.exceptions import (
    EmailProcessingException, InvalidEmailDomainException, AIServiceException
)


router = APIRouter(tags=["emails"])


def get_email_service(request: Request) -> EmailService:
    """Dependency injection for email service with session support."""
    session_id = getattr(request.state, 'session_id', None)
    return EmailService(session_id=session_id)


def get_gmail_service(request: Request) -> GmailService:
    """Dependency injection for Gmail service with session support."""
    session_id = getattr(request.state, 'session_id', None)
    return GmailService(session_id=session_id)


def get_ai_service(request: Request, gmail_service: GmailService = Depends(get_gmail_service)) -> AIService:
    """Dependency injection for AI service with Gmail service dependency."""
    return AIService(gmail_service)


@router.get("/domains", response_model=List[EmailDomain])
async def get_email_domains(
    request: Request,
    email_service: EmailService = Depends(get_email_service)
) -> List[EmailDomain]:
    """
    Get all email domains with importance scores.
    
    Returns:
        List of email domains sorted by importance
    """
    try:
        domains = email_service.get_all_domains()
        return domains
    except EmailProcessingException as e:
        raise HTTPException(status_code=500, detail=f"Failed to get domains: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/domains/{domain}/emails", response_model=List[EmailContent])
async def get_emails_by_domain(
    request: Request,
    domain: str,
    limit: int = 20,
    email_service: EmailService = Depends(get_email_service)
) -> List[EmailContent]:
    """
    Get recent emails from a specific domain.
    
    Args:
        domain: Email domain to filter by
        limit: Maximum number of emails to return (default: 20)
    
    Returns:
        List of emails from the specified domain
    """
    try:
        if limit > 100:  # Prevent excessive requests
            limit = 100
        
        emails = email_service.get_emails_by_domain(domain, limit)
        return emails
    except EmailProcessingException as e:
        raise HTTPException(status_code=500, detail=f"Failed to get emails: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/summarize", response_model=EmailSummary)
async def summarize_email(
    request: Request,
    email: EmailContent,
    ai_service: AIService = Depends(get_ai_service)
) -> EmailSummary:
    """
    Generate AI summary for an email.
    
    Args:
        email: Email content to summarize
    
    Returns:
        AI-generated email summary with key points and analysis
    """
    try:
        summary = await ai_service.summarize_email(email)
        return summary
    except AIServiceException as e:
        raise HTTPException(status_code=500, detail=f"AI summarization failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate-response", response_model=ResponseGeneration)
async def generate_email_response(
    request: Request,
    response_request: ResponseRequest,
    ai_service: AIService = Depends(get_ai_service)
) -> ResponseGeneration:
    """
    Generate AI-powered email response.
    
    Args:
        request: Response generation request with original email and user input
    
    Returns:
        Generated email response with confidence score
    """
    try:
        response = await ai_service.generate_response(response_request)
        return response
    except AIServiceException as e:
        raise HTTPException(status_code=500, detail=f"Response generation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/send-reply")
async def send_email_reply(
    request: Request,
    reply_request: dict,
    email_service: EmailService = Depends(get_email_service)
) -> dict:
    """
    Send a reply to an email.
    
    Args:
        request: Dict containing original_email and reply_body
    
    Returns:
        Success confirmation
    """
    try:
        original_email = EmailContent(**reply_request.get('original_email'))
        reply_body = reply_request.get('reply_body', '')
        
        if not reply_body.strip():
            raise HTTPException(status_code=400, detail="Reply body cannot be empty")
        
        success = email_service.send_reply(original_email, reply_body)
        
        if success:
            return {"message": "Reply sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send reply")
            
    except EmailProcessingException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/message/{message_id}", response_model=EmailContent)
async def get_full_email(
    request: Request,
    message_id: str,
    email_service: EmailService = Depends(get_email_service)
) -> EmailContent:
    """
    Get full email content by message ID.
    
    Args:
        message_id: Gmail message ID
    
    Returns:
        Full email content with body
    """
    try:
        email = email_service.get_email_by_id(message_id)
        return email
    except EmailProcessingException as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Service health status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "email-ai-backend",
            "version": "1.0.0"
        }
    ) 