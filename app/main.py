"""
Main application file for the Server Management API.

This module initializes the FastAPI application, sets up metadata
(title, description, version), defines a basic health check endpoint,
and includes the routers containing the business logic for managing server resources.

The application serves as the entry point for the RESTful API.

Routers Included:
- servers: Handles CRUD operations for server resources (defined in app.routers.servers).
"""
import logging
from fastapi import FastAPI
from app.logging_config import setup_logging
from app.routers import servers

# Setup logging before anything else
setup_logging(log_level="INFO", log_file="logs/app.log")

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Server Management API",
    description="RESTful API for managing servers in datacenters",
    version="1.0.0"
)


# Health check endpoint
@app.get("/health", tags=["health"])
def health_check():
    """
    Status check to verify the service is running.

    Returns a simple message indicating the service is operational.
    """
    return {"status": "ok", "message": "Service is running"}


# Include server router
app.include_router(servers.router)


@app.on_event("startup")
async def startup_event():
    """
    Handles events that occur when the **application starts up**.
    Used for initializing resources, configurations, or logging.
    """
    logger.info("Application starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Handles events that occur when the **application is shutting down**.
    Used for cleaning up resources, closing connections, or logging.
    """
    logger.info("Application shutting down")


@app.get("/")
def root():
    """
    **Root endpoint** for the Server Management API.

    Returns:
        dict: A simple dictionary with a welcome message.
    """
    return {"message": "Server Management API"}
