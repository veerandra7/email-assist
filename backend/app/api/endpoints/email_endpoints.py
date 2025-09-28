"""
Email-related API endpoints.
Follows Single Responsibility Principle - handles only email API operations.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
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


router = APIRouter(prefix="/api/emails", tags=["emails"])


def get_email_service() -> EmailService:
    """Dependency injection for email service."""
    return EmailService()


def get_ai_service() -> AIService:
    """Dependency injection for AI service."""
    return AIService()


def get_gmail_service() -> GmailService:
    """Dependency injection for Gmail service."""
    return GmailService()


@router.get("/domains", response_model=List[EmailDomain])
async def get_email_domains(
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
    request: ResponseRequest,
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
        response = await ai_service.generate_response(request)
        return response
    except AIServiceException as e:
        raise HTTPException(status_code=500, detail=f"Response generation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/send-reply")
async def send_email_reply(
    request: dict,
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
        original_email = EmailContent(**request.get('original_email'))
        reply_body = request.get('reply_body', '')
        
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