"""
Configuration management for the email AI application.
Follows Single Responsibility Principle - handles only configuration.
"""
import os
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # API Keys
    claude_api_key: Optional[str] = None
    
    # Gmail OAuth2 Configuration
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_redirect_uri: str = "http://localhost:8000/auth/gmail/callback"
    gmail_scopes: list = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose"
    ]
    

    
    # Application Settings
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # AI Service Configuration
    max_email_length: int = 10000
    max_response_length: int = 2000
    
    # Gmail API Performance Settings
    gmail_request_timeout: int = 30  # seconds
    gmail_max_emails_per_request: int = 30  # reduced for better performance
    
    # CORS Settings
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3030,http://127.0.0.1:3030,http://frontend:3000"
    
    @property
    def cors_origins(self) -> list:
        """Parse CORS origins from string to list."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",")]
        return self.allowed_origins
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator('claude_api_key')
    def validate_claude_api_key(cls, v):
        if not v:
            print("Warning: Claude API key not set. AI features will not work.")
        return v


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
