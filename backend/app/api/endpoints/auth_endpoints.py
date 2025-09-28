"""
Authentication-related API endpoints.
Handles Gmail OAuth2 authentication flow.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Any

from app.services.gmail_service import GmailService
from app.core.exceptions import EmailProcessingException


router = APIRouter(tags=["authentication"])


def get_gmail_service() -> GmailService:
    """Dependency injection for Gmail service."""
    return GmailService()


@router.get("/gmail/url")
async def get_gmail_auth_url(
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
    code: str = Query(..., description="Authorization code from Gmail"),
    gmail_service: GmailService = Depends(get_gmail_service)
):
    """
    Handle Gmail OAuth2 callback.
    
    Args:
        code: Authorization code from Gmail OAuth2 flow
    
    Returns:
        Redirect to frontend with success/error status
    """
    try:
        success = gmail_service.authenticate_with_code(code)
        if success:
            # Redirect to frontend with success
            return RedirectResponse(
                url="http://localhost:3000?auth=success",
                status_code=302
            )
        else:
            return RedirectResponse(
                url="http://localhost:3000?auth=error&message=authentication_failed",
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
    gmail_service: GmailService = Depends(get_gmail_service)
) -> Dict[str, Any]:
    """
    Check Gmail authentication status.
    
    Returns:
        Authentication status and user profile if authenticated
    """
    try:
        if gmail_service.is_authenticated():
            profile = gmail_service.get_user_profile()
            return {
                "authenticated": True,
                "user_profile": profile
            }
        else:
            return {"authenticated": False}
    except EmailProcessingException as e:
        return {
            "authenticated": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "authenticated": False,
            "error": "Failed to check authentication status"
        }


@router.post("/gmail/logout")
async def gmail_logout() -> Dict[str, str]:
    """
    Logout from Gmail (clear stored credentials).
    
    Returns:
        Logout confirmation
    """
    try:
        import os
        
        # Remove credential files
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