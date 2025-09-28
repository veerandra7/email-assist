"""
Pydantic models for email-related data structures.
Follows Single Responsibility Principle - handles only data models.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, validator
from enum import Enum


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EmailDomain(BaseModel):
    """Email domain information."""
    domain: str
    count: int
    importance_score: float
    last_received: Optional[datetime] = None
    
    @validator('importance_score')
    def validate_importance_score(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Importance score must be between 0 and 1')
        return v


class EmailContent(BaseModel):
    """Email content structure."""
    subject: str
    body: str
    sender: EmailStr
    recipient: EmailStr
    received_date: datetime
    priority: EmailPriority = EmailPriority.MEDIUM
    domain: str
    
    @validator('body')
    def validate_body_length(cls, v):
        if len(v) > 10000:  # Max length from config
            raise ValueError('Email body too long')
        return v


class EmailSummary(BaseModel):
    """AI-generated email summary."""
    original_email: EmailContent
    summary: str
    key_points: List[str]
    action_required: bool
    urgency_level: EmailPriority
    suggested_response_tone: str


class ResponseRequest(BaseModel):
    """Request for generating email response."""
    original_email: EmailContent
    user_input: str
    tone: Optional[str] = "professional"
    
    @validator('user_input')
    def validate_user_input(cls, v):
        if not v.strip():
            raise ValueError('User input cannot be empty')
        return v


class ResponseGeneration(BaseModel):
    """Generated email response."""
    original_email: EmailContent
    user_input: str
    generated_response: str
    confidence_score: float
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence score must be between 0 and 1')
        return v


class DomainAnalysis(BaseModel):
    """Analysis of email domains."""
    domains: List[EmailDomain]
    total_emails: int
    analysis_date: datetime 