"""
Main application file for the Server Management API (Async Version).

This module initializes the FastAPI application with async support,
creates a database connection pool at startup, and manages cleanup at shutdown.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.logging_config import setup_logging
from app.routers import servers
from app.database import create_pool, close_pool

# Setup logging before anything else
setup_logging(log_level="INFO", log_file="logs/app.log")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):  # pylint: disable=unused-argument
    """
    Async context manager for application lifespan.
    Handles startup and shutdown events in one place (modern FastAPI approach).

    Args:
        app_instance: The FastAPI application (required by FastAPI but not used here)
    """
    # Startup: Create database connection pool
    logger.info("Application starting up - creating database pool")
    await create_pool()
    logger.info("Database pool created successfully")

    yield  # Application runs here

    # Shutdown: Close database pool
    logger.info("Application shutting down - closing database pool")
    await close_pool()
    logger.info("Database pool closed successfully")


app = FastAPI(
    title="Server Management API",
    description="RESTful API for managing servers in datacenters (Async)",
    version="2.0.0",
    lifespan=lifespan  # Use lifespan instead of startup/shutdown events
)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Status check to verify the service is running.
    Now returns async!
    """
    return {"status": "ok", "message": "Service is running (async mode)"}


# Include server router
app.include_router(servers.router)


@app.get("/")
async def root():
    """
    Root endpoint for the Server Management API.
    """
    return {"message": "Server Management API (Async)"}
