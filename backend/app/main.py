"""
Main FastAPI application entry point.
Follows Single Responsibility Principle - handles only application setup.
"""
import logging
import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import settings
from app.core.exceptions import EmailAIException
from app.api.endpoints import email_endpoints, ai_endpoints, auth_endpoints

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


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    Factory pattern for application creation.
    """
    logger.info("🚀 Starting Email AI Assistant application...")
    
    app = FastAPI(
        title="Email AI Assistant",
        description="AI-powered email management and response system",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    logger.info("✅ FastAPI application instance created")
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        return response
    
    # Configure CORS
    logger.info(f"🔧 Configuring CORS with origins: {settings.cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    logger.info("✅ CORS middleware configured")
    
    # Include routers
    logger.info("🔌 Registering API routers...")
    app.include_router(auth_endpoints.router)
    logger.info("✅ Auth endpoints registered")
    app.include_router(email_endpoints.router)
    logger.info("✅ Email endpoints registered")
    app.include_router(ai_endpoints.router)
    logger.info("✅ AI endpoints registered")
    
    # Global exception handler
    @app.exception_handler(EmailAIException)
    async def email_ai_exception_handler(request: Request, exc: EmailAIException):
        logger.error(f"❌ EmailAI Exception: {type(exc).__name__}: {str(exc)} - Path: {request.url.path}")
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "type": type(exc).__name__}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"💥 Unhandled Exception: {type(exc).__name__}: {str(exc)} - Path: {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": "InternalServerError"}
        )
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("🎯 Application startup complete!")
        logger.info(f"📋 Environment: {'Development' if settings.debug else 'Production'}")
        logger.info(f"🌐 Host: {settings.host}:{settings.port}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🔄 Application shutting down...")
    
    # Root endpoint
    @app.get("/")
    async def root():
        logger.info("🏠 Root endpoint accessed")
        return JSONResponse(
            content={
                "message": "Email AI Assistant API",
                "version": "1.0.0",
                "docs": "/docs",
                "health": "/api/emails/health"
            }
        )
    
    logger.info("🎉 Application configuration complete!")
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting uvicorn server...")
    logger.info(f"📍 Server will run on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 