"""
Main application file for the Server Management API.

This module initializes the FastAPI application, sets up metadata
(title, description, version), defines a basic health check endpoint,
and includes the routers containing the business logic for managing server resources.

The application serves as the entry point for the RESTful API.

Routers Included:
- servers: Handles CRUD operations for server resources (defined in app.routers.servers).
"""
from fastapi import FastAPI
from app.routers import servers

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
