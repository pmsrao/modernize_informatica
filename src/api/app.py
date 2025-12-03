"""FastAPI App — Production Style"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from utils.logger import get_logger
from .routes import router

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    description="API for Informatica to Databricks modernization accelerator"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.get("/health")
def health():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "version": settings.api_version,
        "service": "Informatica Modernization Accelerator"
    }

@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health"
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"API running on {settings.api_host}:{settings.api_port}")
    logger.info("API routes registered")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down API")
