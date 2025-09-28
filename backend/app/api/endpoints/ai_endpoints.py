"""
AI-related API endpoints.
Follows Single Responsibility Principle - handles only AI API operations.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.services.ai_service import AIService
from app.core.exceptions import AIServiceException, APIKeyMissingException

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


def get_ai_service() -> AIService:
    """Dependency injection for AI service."""
    logger.debug("🔧 Creating AI service instance for dependency injection")
    try:
        service = AIService()
        logger.debug("✅ AI service instance created successfully")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to create AI service instance: {str(e)}")
        raise


@router.get("/provider")
async def get_ai_provider(
    ai_service: AIService = Depends(get_ai_service)
) -> JSONResponse:
    """
    Get the current AI provider being used.
    
    Returns:
        Current AI provider information
    """
    logger.info("📋 API: Getting current AI provider information")
    
    try:
        provider_name = ai_service.get_provider_name()
        logger.info(f"✅ AI provider retrieved: {provider_name}")
        
        response_data = {
            "provider": provider_name,
            "status": "active"
        }
        
        logger.debug(f"📤 Returning provider response: {response_data}")
        return JSONResponse(content=response_data)
        
    except APIKeyMissingException as e:
        logger.error(f"❌ AI service unavailable - API key missing: {str(e)}")
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"💥 Unexpected error in get_ai_provider: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def ai_health_check(
    ai_service: AIService = Depends(get_ai_service)
) -> JSONResponse:
    """
    Health check for AI service.
    
    Returns:
        AI service health status
    """
    logger.info("🩺 API: Performing AI service health check")
    
    try:
        provider_name = ai_service.get_provider_name()
        logger.info(f"✅ AI service health check passed - Provider: {provider_name}")
        
        response_data = {
            "status": "healthy",
            "provider": provider_name,
            "service": "ai-service",
            "capabilities": ["email_summarization", "response_generation"]
        }
        
        logger.debug(f"📤 Returning health check response: {response_data}")
        return JSONResponse(content=response_data)
        
    except APIKeyMissingException as e:
        logger.warning(f"⚠️ AI service unhealthy - API key missing: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "service": "ai-service"
            }
        )
    except Exception as e:
        logger.error(f"💥 AI service health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Internal server error",
                "service": "ai-service"
            }
        ) 