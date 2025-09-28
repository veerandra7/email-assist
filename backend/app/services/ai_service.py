"""
AI service for email summarization and response generation.
Follows Single Responsibility Principle - handles only AI operations.
Uses Claude API for all AI operations with YAML-based prompt management.
"""
import logging
import time
import yaml
import os
from typing import List, Dict, Any
import anthropic

from app.models.email_models import (
    EmailContent, EmailSummary, ResponseRequest, ResponseGeneration, EmailPriority
)
from app.core.config import get_settings
from app.core.exceptions import AIServiceException, APIKeyMissingException

# Configure logger
logger = logging.getLogger(__name__)

# Get settings instance
settings = get_settings()


class PromptManager:
    """Manages prompt templates from YAML configuration."""
    
    def __init__(self, prompts_file_path: str):
        """Initialize prompt manager with YAML file."""
        self.prompts_file_path = prompts_file_path
        self.prompts_config = self._load_prompts()
        logger.info("📋 PromptManager initialized with YAML configuration")
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from YAML file."""
        try:
            with open(self.prompts_file_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info(f"✅ Loaded prompts configuration from {self.prompts_file_path}")
                return config
        except FileNotFoundError:
            logger.error(f"❌ Prompts file not found: {self.prompts_file_path}")
            raise AIServiceException(f"Prompts file not found: {self.prompts_file_path}")
        except yaml.YAMLError as e:
            logger.error(f"❌ Error parsing YAML prompts file: {str(e)}")
            raise AIServiceException(f"Error parsing YAML prompts file: {str(e)}")
    
    def get_prompt(self, prompt_name: str) -> str:
        """Get a specific prompt template."""
        try:
            prompt_config = self.prompts_config['prompts'][prompt_name]
            template = prompt_config['template']
            current_version = prompt_config.get('current_version', 'unknown')
            logger.debug(f"📝 Retrieved prompt '{prompt_name}' (current_version: {current_version})")
            return template
        except KeyError as e:
            logger.error(f"❌ Prompt '{prompt_name}' not found in configuration")
            raise AIServiceException(f"Prompt '{prompt_name}' not found in configuration")
    
    def get_prompt_version(self, prompt_name: str) -> str:
        """Get the current version of a specific prompt."""
        try:
            prompt_config = self.prompts_config['prompts'][prompt_name]
            current_version = prompt_config.get('current_version', 'unknown')
            logger.debug(f"📋 Retrieved version for prompt '{prompt_name}': {current_version}")
            return current_version
        except KeyError as e:
            logger.error(f"❌ Prompt '{prompt_name}' not found in configuration")
            raise AIServiceException(f"Prompt '{prompt_name}' not found in configuration")
    
    def get_all_prompt_versions(self) -> Dict[str, str]:
        """Get all prompt names and their current versions."""
        versions = {}
        try:
            for prompt_name, prompt_config in self.prompts_config['prompts'].items():
                current_version = prompt_config.get('current_version', 'unknown')
                versions[prompt_name] = current_version
            logger.debug(f"📋 Retrieved versions for {len(versions)} prompts")
            return versions
        except Exception as e:
            logger.error(f"❌ Error retrieving prompt versions: {str(e)}")
            return {}
    
    def get_config(self, config_key: str, default=None):
        """Get configuration value."""
        return self.prompts_config.get('config', {}).get(config_key, default)


class SignatureExtractor:
    """Extracts sender names from email for signature generation."""
    
    def __init__(self, gmail_service=None):
        """Initialize with Gmail service for user profile access."""
        self.gmail_service = gmail_service
    
    @staticmethod
    def extract_sender_name(email: EmailContent) -> str:
        """Extract sender name from email address."""
        logger.debug(f"🔍 Extracting sender name from: {email.sender}")
        
        # Extract name from email address
        email_address = str(email.sender)
        
        # Try to extract name from email format like "John Doe <john@example.com>"
        if '<' in email_address and '>' in email_address:
            name_part = email_address.split('<')[0].strip()
            if name_part:
                logger.debug(f"📝 Extracted name from email format: {name_part}")
                return name_part
        
        # Extract name from email address (before @)
        local_part = email_address.split('@')[0]
        domain_part = email_address.split('@')[1] if '@' in email_address else ''
        
        # Handle common business/service email patterns
        business_patterns = {
            'hi': 'Team',
            'hello': 'Team', 
            'info': 'Team',
            'support': 'Support Team',
            'noreply': 'Team',
            'no-reply': 'Team',
            'admin': 'Admin Team',
            'contact': 'Team'
        }
        
        # Check if it's a business email pattern
        if local_part.lower() in business_patterns:
            # Extract company name from domain
            domain_name = domain_part.split('.')[0] if '.' in domain_part else domain_part
            company_name = domain_name.replace('-', ' ').replace('_', ' ').title()
            logger.debug(f"📝 Extracted business sender: {company_name} {business_patterns[local_part.lower()]}")
            return f"{company_name} {business_patterns[local_part.lower()]}"
        
        # Convert common email formats to names
        if '.' in local_part:
            # john.doe -> John Doe
            name_parts = local_part.split('.')
            formatted_name = ' '.join(part.capitalize() for part in name_parts)
            logger.debug(f"📝 Formatted name from email: {formatted_name}")
            return formatted_name
        else:
            # john -> John
            formatted_name = local_part.capitalize()
            logger.debug(f"📝 Formatted name from email: {formatted_name}")
            return formatted_name
    
    def extract_reply_sender_name(self) -> str:
        """Extract the name of the person sending the reply (current authenticated user)."""
        try:
            # Check if Gmail service is available
            if not self.gmail_service:
                logger.warning("⚠️ Gmail service not available, using fallback name")
                return "User"
            
            # Get the authenticated user's profile from Gmail
            if not self.gmail_service.is_authenticated():
                logger.warning("⚠️ Gmail not authenticated, using fallback name")
                return "User"
            
            profile = self.gmail_service.get_user_profile()
            user_email = profile.get('email', '')
            
            if user_email:
                logger.debug(f"🔍 Extracting reply sender name from authenticated email: {user_email}")
                
                # Use the same extraction logic as for regular emails
                local_part = user_email.split('@')[0]
                
                # Convert common email formats to names
                if '.' in local_part:
                    # john.doe -> John Doe
                    name_parts = local_part.split('.')
                    formatted_name = ' '.join(part.capitalize() for part in name_parts)
                    logger.debug(f"📝 Extracted reply sender name: {formatted_name}")
                    return formatted_name
                else:
                    # john -> John
                    formatted_name = local_part.capitalize()
                    logger.debug(f"📝 Extracted reply sender name: {formatted_name}")
                    return formatted_name
            else:
                logger.warning("⚠️ Could not get user email from profile, using fallback")
                return "User"
                
        except Exception as e:
            logger.error(f"❌ Error extracting reply sender name: {e}")
            return "User"  # Fallback


class ClaudeProvider:
    """Claude API provider implementation with YAML prompt support."""
    
    def __init__(self, api_key: str, prompt_manager: PromptManager, gmail_service=None):
        logger.info("🔧 Initializing Claude API provider...")
        if not api_key:
            logger.error("❌ Claude API key is missing")
            raise APIKeyMissingException("Claude API key is required")
        
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.prompt_manager = prompt_manager
            self.signature_extractor = SignatureExtractor(gmail_service) if gmail_service else SignatureExtractor(None)
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
            prompt_version = self.prompt_manager.get_prompt_version('summarization')
            logger.debug(f"🤖 Generated prompt for summarization (version: {prompt_version}, length: {len(prompt)} chars)")
            
            max_tokens = self.prompt_manager.get_config('max_tokens_summarization', 500)
            model = self.prompt_manager.get_config('model', 'claude-sonnet-4-20250514')
            
            logger.info("🔄 Sending request to Claude API for summarization...")
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
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
            prompt_name = self._get_response_prompt_name(request.tone)
            prompt_version = self.prompt_manager.get_prompt_version(prompt_name)
            logger.debug(f"🤖 Generated prompt for response (version: {prompt_version}, length: {len(prompt)} chars)")
            
            max_tokens = self.prompt_manager.get_config('max_tokens_response', 300)
            model = self.prompt_manager.get_config('model', 'claude-sonnet-4-20250514')
            
            logger.info("🔄 Sending request to Claude API for response generation...")
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
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
    
    def _get_response_prompt_name(self, tone: str) -> str:
        """Get the appropriate prompt name based on tone."""
        if tone:
            tone_lower = tone.lower()
            if tone_lower == "formal":
                return "response_generation_formal"
            elif tone_lower == "friendly":
                return "response_generation_friendly"
            elif tone_lower == "urgent":
                return "response_generation_urgent"
            elif tone_lower == "apologetic":
                return "response_generation_apologetic"
        return "response_generation"    
    def _create_summary_prompt(self, email: EmailContent) -> str:
        """Create prompt for email summarization using YAML template."""
        logger.debug("📝 Creating summarization prompt from YAML template...")
        template = self.prompt_manager.get_prompt('summarization')
        
        return template.format(
            subject=email.subject,
            sender=email.sender,
            received_date=email.received_date,
            body=email.body
        )
    
    def _create_response_prompt(self, request: ResponseRequest) -> str:
        """Create prompt for response generation using YAML template."""
        logger.debug("📝 Creating response generation prompt from YAML template...")
        
        # Extract original sender name (from the email we're replying to)
        original_sender_name = self.signature_extractor.extract_sender_name(request.original_email)
        logger.debug(f"👤 Using original sender name: {original_sender_name}")
        
        # Extract reply sender name (the person sending the reply)
        reply_sender_name = self.signature_extractor.extract_reply_sender_name()
        logger.debug(f"✍️ Using reply sender name: {reply_sender_name}")
        
        # Choose appropriate prompt based on tone
        prompt_name = self._get_response_prompt_name(request.tone)
        template = self.prompt_manager.get_prompt(prompt_name)
        
        return template.format(
            subject=request.original_email.subject,
            sender=request.original_email.sender,
            body=request.original_email.body,
            user_input=request.user_input,
            tone=request.tone or 'professional',
            original_sender_name=original_sender_name,
            reply_sender_name=reply_sender_name
        )
    
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
    Follows Single Responsibility Principle with YAML prompt management.
    """
    
    def __init__(self, gmail_service=None):
        """Initialize AI service with Claude provider and prompt manager."""
        logger.info("🤖 Initializing AI Service...")
        
        if not settings.claude_api_key or settings.claude_api_key == "your_claude_api_key_here":
            logger.error("❌ Claude API key not configured in settings")
            raise APIKeyMissingException("Claude API key not configured. Please set CLAUDE_API_KEY in your .env file")
        
        try:
            # Store Gmail service for signature extraction
            self.gmail_service = gmail_service
            
            # Initialize prompt manager
            prompts_file_path = os.path.join(os.path.dirname(__file__), 'prompts.yaml')
            prompt_manager = PromptManager(prompts_file_path)
            
            # Initialize Claude provider with Gmail service for signature extraction
            self.provider = ClaudeProvider(settings.claude_api_key, prompt_manager, gmail_service)
            logger.info("✅ AI Service initialized successfully with Claude provider and YAML prompts")
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
    
    def get_prompt_versions(self) -> Dict[str, str]:
        """Get all prompt versions for monitoring and debugging."""
        return self.provider.prompt_manager.get_all_prompt_versions()
    
    def get_prompt_version(self, prompt_name: str) -> str:
        """Get the current version of a specific prompt."""
        return self.provider.prompt_manager.get_prompt_version(prompt_name)
