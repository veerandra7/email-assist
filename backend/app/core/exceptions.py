"""
Custom exceptions for the email AI application.
Follows Single Responsibility Principle - handles only exception definitions.
"""


class EmailAIException(Exception):
    """Base exception for the email AI application."""
    pass


class AIServiceException(EmailAIException):
    """Exception raised when AI service encounters an error."""
    pass


class EmailProcessingException(EmailAIException):
    """Exception raised when email processing fails."""
    pass


class InvalidEmailDomainException(EmailAIException):
    """Exception raised when email domain is invalid."""
    pass


class APIKeyMissingException(EmailAIException):
    """Exception raised when required API key is missing."""
    pass


class EmailContentTooLongException(EmailAIException):
    """Exception raised when email content exceeds maximum length."""
    pass 