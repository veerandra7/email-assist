"""
Main FastAPI application entry point.
Follows Single Responsibility Principle - handles only application setup.
"""
import logging
import os
import sys
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import get_settings
from app.core.exceptions import EmailAIException
from app.core.session_manager import session_manager
from app.api.endpoints import email_endpoints, ai_endpoints, auth_endpoints
from app.startup import clear_gmail_sessions

# Configure logging
log_handlers = [logging.StreamHandler(sys.stdout)]

# Only add file handler if not in container (for local development)
if not os.getenv('DOCKER_CONTAINER'):
    log_handlers.append(logging.FileHandler('app.log'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=log_handlers
)

logger = logging.getLogger(__name__)

# Get settings instance
settings = get_settings()

def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    logger.info("🚀 Starting Email AI Assistant application...")
    
    # Create FastAPI app
    app = FastAPI(
        title="Email AI Assistant",
        description="AI-powered email management and response generation",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
    )
    
    logger.info("✅ FastAPI application instance created")
    
    # Add CORS middleware
    logger.info(f"🔧 Configuring CORS with origins: {settings.cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("✅ CORS middleware configured")
    
    # Add session management middleware
    @app.middleware("http")
    async def session_middleware(request: Request, call_next):
        """Middleware to handle session management."""
        # Get tab ID from header (sent by frontend)
        tab_id = request.headers.get("X-Tab-ID")
        
        # Special handling for OAuth callback - use state parameter to find session
        if request.url.path == "/auth/gmail/callback":
            state = request.query_params.get("state")
            if state and state != "no_session" and session_manager.is_valid_session(state):
                session_id = state
                logger.info(f"🔗 OAuth callback using session from state: {session_id}")
            else:
                # Fallback for callback without valid state
                session_id = session_manager.create_session()
                logger.warning(f"⚠️ OAuth callback with invalid state, created new session: {session_id}")
        elif tab_id:
            # Regular tab-specific session handling
            session_id = tab_id
            if not session_manager.is_valid_session(session_id):
                session_manager.create_session_with_id(session_id)
                logger.info(f"🆕 Created new tab session: {session_id}")
            else:
                logger.debug(f"🔄 Using existing tab session: {session_id}")
        else:
            # Fallback: use cookie-based session
            session_id = request.cookies.get("session_id")
            if not session_id or not session_manager.is_valid_session(session_id):
                session_id = session_manager.create_session()
                logger.info(f"🆕 Created new cookie session: {session_id}")
            else:
                logger.debug(f"🔄 Using existing cookie session: {session_id}")
        
        request.state.session_id = session_id
        response = await call_next(request)
        
        # Set session cookie for non-tab-based requests
        if not tab_id and request.url.path != "/auth/gmail/callback":
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=False,  # Allow JavaScript access
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                max_age=None  # Session cookie - expires when browser closes
            )
        
        return response
    
    # Register API routers
    logger.info("🔌 Registering API routers...")
    app.include_router(auth_endpoints.router, prefix="/auth", tags=["authentication"])
    logger.info("✅ Auth endpoints registered")
    
    app.include_router(email_endpoints.router, prefix="/api/emails", tags=["emails"])
    logger.info("✅ Email endpoints registered")
    
    app.include_router(ai_endpoints.router, prefix="/api/ai", tags=["ai"])
    logger.info("✅ AI endpoints registered")
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        return response
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"❌ Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": "InternalServerError"}
        )
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        # Clear Gmail sessions on startup for fresh authentication
        clear_gmail_sessions()
        logger.info("🎯 Application startup complete!")
        logger.info(f"📋 Environment: {'Development' if settings.debug else 'Production'}")
        logger.info(f"�� Host: {settings.host}:{settings.port}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🔄 Application shutting down...")
    
    # Root endpoint
    @app.get("/")
    async def root():
        logger.info("🏠 Root endpoint accessed")
        return {
            "message": "Email AI Assistant API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if settings.debug else "disabled"
        }
    
    logger.info("🎉 Application configuration complete!")
    return app

# Create app instance
app = create_application()

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"📍 Server will run on {settings.host}:{settings.port}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
