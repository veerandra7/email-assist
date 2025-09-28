"""
AI service for email summarization and response generation.
Follows Single Responsibility Principle - handles only AI operations.
Uses Claude API for all AI operations.
"""
import logging
import time
from typing import List
import anthropic

from app.models.email_models import (
    EmailContent, EmailSummary, ResponseRequest, ResponseGeneration, EmailPriority
)
from app.core.config import settings
from app.core.exceptions import AIServiceException, APIKeyMissingException

# Configure logger
logger = logging.getLogger(__name__)


class ClaudeProvider:
    """Claude API provider implementation."""
    
    def __init__(self, api_key: str):
        logger.info("🔧 Initializing Claude API provider...")
        if not api_key:
            logger.error("❌ Claude API key is missing")
            raise APIKeyMissingException("Claude API key is required")
        
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Claude API client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Claude client: {str(e)}")
            raise AIServiceException(f"Failed to initialize Claude client: {str(e)}")
    
    async def summarize_email(self, email: EmailContent) -> EmailSummary:
        """Summarize email using Claude."""
        start_time = time.time()
        logger.info(f"📄 Starting email summarization for email from {email.sender}")
        logger.debug(f"📧 Email details - Subject: '{email.subject}', Body length: {len(email.body)} chars")
        
        try:
            prompt = self._create_summary_prompt(email)
            logger.debug(f"🤖 Generated prompt for summarization (length: {len(prompt)} chars)")
            
            logger.info("🔄 Sending request to Claude API for summarization...")
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Claude API response received in {processing_time:.3f}s")
            
            content = response.content[0].text
            logger.debug(f"📝 Claude response length: {len(content)} chars")
            
            summary = self._parse_summary_response(content, email)
            logger.info(f"🎯 Email summarization completed - Urgency: {summary.urgency_level}, Action Required: {summary.action_required}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Claude summarization failed: {str(e)}", exc_info=True)
            raise AIServiceException(f"Claude summarization failed: {str(e)}")
    
    async def generate_response(self, request: ResponseRequest) -> ResponseGeneration:
        """Generate email response using Claude."""
        start_time = time.time()
        logger.info(f"✍️ Starting response generation for email from {request.original_email.sender}")
        logger.info(f"📋 User instructions: '{request.user_input}' | Tone: {request.tone}")
        
        try:
            prompt = self._create_response_prompt(request)
            logger.debug(f"🤖 Generated prompt for response (length: {len(prompt)} chars)")
            
            logger.info("🔄 Sending request to Claude API for response generation...")
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Claude API response received in {processing_time:.3f}s")
            
            generated_text = response.content[0].text.strip()
            logger.info(f"📝 Generated response length: {len(generated_text)} chars")
            
            result = ResponseGeneration(
                original_email=request.original_email,
                user_input=request.user_input,
                generated_response=generated_text,
                confidence_score=0.88  # Mock confidence score
            )
            
            logger.info(f"🎉 Response generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Claude response generation failed: {str(e)}", exc_info=True)
            raise AIServiceException(f"Claude response generation failed: {str(e)}")
    
    def _create_summary_prompt(self, email: EmailContent) -> str:
        """Create prompt for email summarization."""
        logger.debug("📝 Creating summarization prompt...")
        return f"""
Analyze this email and provide a structured summary:

Subject: {email.subject}
From: {email.sender}
Date: {email.received_date}
Content: {email.body}

Please provide:
1. A concise 2-3 sentence summary
2. Key points (bullet format)
3. Whether action is required (Yes/No)
4. Urgency level (low/medium/high/urgent)
5. Suggested response tone (professional/friendly/urgent/formal)

Format your response clearly with labels.
"""
    
    def _create_response_prompt(self, request: ResponseRequest) -> str:
        """Create prompt for response generation."""
        logger.debug("📝 Creating response generation prompt...")
        return f"""
Create an email response with the following context:

Original Email Subject: {request.original_email.subject}
From: {request.original_email.sender}
Original Content: {request.original_email.body}

User Instructions: {request.user_input}
Required Tone: {request.tone}

Generate a well-structured email response that addresses the user's instructions while maintaining the specified tone. Keep it professional and concise.
"""
    
    def _parse_summary_response(self, content: str, email: EmailContent) -> EmailSummary:
        """Parse Claude response into EmailSummary object."""
        logger.debug("🔍 Parsing Claude summary response...")
        
        # Similar parsing logic as OpenAI but adapted for Claude's response format
        summary = self._extract_section(content, ["summary", "1."])
        key_points = self._extract_key_points(content)
        action_required = self._extract_action_required(content)
        urgency_level = self._extract_urgency(content)
        suggested_tone = self._extract_suggested_tone(content)
        
        logger.debug(f"📊 Parsed summary - Points: {len(key_points)}, Action: {action_required}, Urgency: {urgency_level}")
        
        return EmailSummary(
            original_email=email,
            summary=summary,
            key_points=key_points,
            action_required=action_required,
            urgency_level=urgency_level,
            suggested_response_tone=suggested_tone
        )
    
    def _extract_section(self, content: str, keywords: List[str]) -> str:
        """Extract a section from the response."""
        lines = content.split('\n')
        for line in lines:
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    return line.split(':', 1)[-1].strip() if ':' in line else line.strip()
        return "Not available"
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from the response."""
        points = []
        lines = content.split('\n')
        in_points_section = False
        
        for line in lines:
            line = line.strip()
            if "key points" in line.lower() or "2." in line:
                in_points_section = True
                continue
            if in_points_section and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                points.append(line.lstrip('•-* '))
            elif in_points_section and line and not any(x in line.lower() for x in ['action', 'urgency', 'tone']):
                points.append(line)
            elif in_points_section and any(x in line.lower() for x in ['action', 'urgency', 'tone']):
                break
        
        return points if points else ["No key points identified"]
    
    def _extract_action_required(self, content: str) -> bool:
        """Extract action required from the response."""
        action_line = self._extract_section(content, ["action", "3."])
        result = "yes" in action_line.lower() or "required" in action_line.lower()
        logger.debug(f"🎯 Action required extracted: {result}")
        return result
    
    def _extract_urgency(self, content: str) -> EmailPriority:
        """Extract urgency level from the response."""
        urgency_line = self._extract_section(content, ["urgency", "4."])
        urgency_text = urgency_line.lower()
        
        if "urgent" in urgency_text:
            result = EmailPriority.URGENT
        elif "high" in urgency_text:
            result = EmailPriority.HIGH
        elif "low" in urgency_text:
            result = EmailPriority.LOW
        else:
            result = EmailPriority.MEDIUM
        
        logger.debug(f"⚡ Urgency level extracted: {result}")
        return result
    
    def _extract_suggested_tone(self, content: str) -> str:
        """Extract suggested tone from the response."""
        tone_line = self._extract_section(content, ["tone", "5."])
        result = tone_line.lower() if tone_line != "Not available" else "professional"
        logger.debug(f"🎵 Suggested tone extracted: {result}")
        return result


class AIService:
    """
    Main AI service using Claude for all operations.
    Follows Single Responsibility Principle.
    """
    
    def __init__(self):
        """Initialize AI service with Claude provider."""
        logger.info("🤖 Initializing AI Service...")
        
        if not settings.claude_api_key or settings.claude_api_key == "your_claude_api_key_here":
            logger.error("❌ Claude API key not configured in settings")
            raise APIKeyMissingException("Claude API key not configured. Please set CLAUDE_API_KEY in your .env file")
        
        try:
            self.provider = ClaudeProvider(settings.claude_api_key)
            logger.info("✅ AI Service initialized successfully with Claude provider")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI service: {str(e)}")
            raise
    
    async def summarize_email(self, email: EmailContent) -> EmailSummary:
        """Summarize email using Claude AI."""
        logger.info(f"📧 AI Service: Summarizing email '{email.subject}' from {email.sender}")
        try:
            result = await self.provider.summarize_email(email)
            logger.info("✅ Email summarization completed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ AI Service summarization failed: {str(e)}")
            raise
    
    async def generate_response(self, request: ResponseRequest) -> ResponseGeneration:
        """Generate email response using Claude AI."""
        logger.info(f"✍️ AI Service: Generating response for email '{request.original_email.subject}'")
        try:
            result = await self.provider.generate_response(request)
            logger.info("✅ Response generation completed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ AI Service response generation failed: {str(e)}")
            raise
    
    def get_provider_name(self) -> str:
        """Get the name of the current AI provider."""
        logger.debug("📋 Returning AI provider name: claude")
        return "claude" 