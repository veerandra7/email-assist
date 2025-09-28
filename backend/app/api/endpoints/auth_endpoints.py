"""
Authentication-related API endpoints.
Handles Gmail OAuth2 authentication flow.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Any
from datetime import datetime

from app.services.gmail_service import GmailService
from app.core.exceptions import EmailProcessingException
from app.core.session_manager import session_manager

logger = logging.getLogger(__name__)


router = APIRouter(tags=["authentication"])


def get_gmail_service(request: Request) -> GmailService:
    """Dependency injection for Gmail service with session support."""
    session_id = getattr(request.state, 'session_id', None)
    return GmailService(session_id=session_id)


@router.get("/gmail/url")
async def get_gmail_auth_url(
    request: Request,
    gmail_service: GmailService = Depends(get_gmail_service)
) -> Dict[str, str]:
    """
    Get Gmail OAuth2 authorization URL.
    
    Returns:
        Authorization URL for Gmail OAuth2 flow
    """
    try:
        auth_url = gmail_service.get_auth_url()
        return {"auth_url": auth_url}
    except EmailProcessingException as e:
        raise HTTPException(status_code=500, detail=f"Failed to get auth URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/gmail/callback")
async def gmail_auth_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Gmail"),
    state: str = Query(..., description="Session ID from OAuth state parameter")
):
    """
    Handle Gmail OAuth2 callback.
    
    Args:
        code: Authorization code from Gmail OAuth2 flow
    
    Returns:
        Redirect to frontend with success/error status
    """
    try:
        logger.info(f"🔐 OAuth callback received - Code: {code[:20]}..., State: {state}")
        
        # Use the session ID from state parameter (passed from auth URL)
        target_session_id = state if state != "no_session" else None
        
        if target_session_id and session_manager.is_valid_session(target_session_id):
            logger.info(f"🎯 Valid session found for callback: {target_session_id}")
            # Create Gmail service with the correct session ID
            gmail_service = GmailService(session_id=target_session_id)
            success = gmail_service.authenticate_with_code(code)
            
            if success:
                logger.info(f"🎉 Gmail authentication successful for session: {target_session_id}")
                # Update session with user email
                try:
                    profile = gmail_service.get_user_profile()
                    session_manager.update_session(target_session_id, {
                        "user_email": profile.get("email"),
                        "authenticated_at": datetime.now().isoformat()
                    })
                    logger.info(f"✅ Successfully authenticated session {target_session_id} with {profile.get('email')}")
                except Exception as e:
                    logger.warning(f"Warning: Could not update session with user email: {e}")
                
                # Redirect to frontend with success and session ID
                return RedirectResponse(
                    url=f"http://localhost:3000?auth=success&session_id={target_session_id}",
                    status_code=302
                )
            else:
                logger.error(f"❌ Gmail authentication failed for session: {target_session_id}")
        else:
            logger.error(f"❌ Invalid or missing session for callback. State: {state}, Valid: {session_manager.is_valid_session(target_session_id) if target_session_id else False}")
        
        # If we get here, authentication failed
        return RedirectResponse(
            url="http://localhost:3000?auth=error&message=session_invalid",
            status_code=302
        )
    except EmailProcessingException as e:
        return RedirectResponse(
            url=f"http://localhost:3000?auth=error&message={str(e)}",
            status_code=302
        )
    except Exception as e:
        return RedirectResponse(
            url="http://localhost:3000?auth=error&message=internal_error",
            status_code=302
        )


@router.get("/gmail/status")
async def get_gmail_auth_status(
    request: Request,
    gmail_service: GmailService = Depends(get_gmail_service)
) -> Dict[str, Any]:
    """
    Check Gmail authentication status.
    
    Returns:
        Authentication status and user profile if authenticated
    """
    # Debug logging
    session_id = getattr(request.state, 'session_id', None)
    tab_id = request.headers.get("X-Tab-ID")
    logger.info(f"🔍 Auth status check - Session ID: {session_id}, Tab ID: {tab_id}")
    
    try:
        if gmail_service.is_authenticated():
            profile = gmail_service.get_user_profile()
            logger.info(f"📊 Auth status result - Authenticated: True, User: {profile.get('email', 'Unknown')}")
            return {
                "authenticated": True,
                "user_profile": profile
            }
        else:
            logger.info("📊 Auth status result - Authenticated: False")
            return {"authenticated": False}
    except EmailProcessingException as e:
        logger.error(f"❌ Auth status check failed with EmailProcessingException: {e}")
        return {
            "authenticated": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"❌ Auth status check failed with Exception: {e}")
        return {
            "authenticated": False,
            "error": "Failed to check authentication status"
        }


@router.post("/gmail/logout")
async def gmail_logout(request: Request) -> Dict[str, str]:
    """
    Logout from Gmail (clear stored credentials and session).
    
    Returns:
        Logout confirmation
    """
    try:
        session_id = getattr(request.state, 'session_id', None)
        
        if session_id:
            # Delete the session and its associated credentials
            session_manager.delete_session(session_id)
        else:
            # Fallback: clear global credential files for backward compatibility
            import os
            files_to_remove = ["gmail_credentials.json", "gmail_token.json"]
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        return {"message": "Successfully logged out from Gmail"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to logout: {str(e)}")


@router.get("/health")
async def auth_health_check():
    """
    Health check for authentication service.
    
    Returns:
        Service health status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "auth-service",
            "version": "1.0.0"
        }
    ) 