"""
Database connection utility module with async support.

This module provides an async context manager and connection pool for
PostgreSQL database using `asyncpg` library.

Configuration:
- Database credentials are loaded from environment variables using `dotenv`.
- Environment variables expected:
    - DB_HOST (default: localhost)
    - DB_NAME (default: server_management)
    - DB_USER (default: postgres)
    - DB_PASSWORD (default: postgres)
    - DB_PORT (default: 5432)

Features:
- **Connection Pool**: Reuses connections for better performance
- **Async Operations**: Non-blocking database queries
- **Automatic Transaction Management**: Commits on success, rolls back on error
"""
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncpg

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "server_management"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432"))
}

# Global connection pool
# pylint: disable=invalid-name
_pool = None


async def create_pool():
    """
    Create a connection pool.
    Call this once at application startup.
    """
    global _pool  # pylint: disable=global-statement
    _pool = await asyncpg.create_pool(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        min_size=2,      # Minimum connections in pool
        max_size=10,     # Maximum connections in pool
        command_timeout=60  # Query timeout in seconds
    )
    return _pool


async def close_pool():
    """
    Close the connection pool.
    Call this at application shutdown.
    """
    global _pool  # pylint: disable=global-statement
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_db_connection():
    """
    Async context manager for database connections from pool.

    Usage:
        async with get_db_connection() as conn:
            result = await conn.fetch("SELECT * FROM server")

    The connection is automatically acquired from pool and returned on exit.
    Transactions are committed on success, rolled back on error.
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call create_pool() first.")

    # Acquire connection from pool
    async with _pool.acquire() as conn:
        # Start a transaction
        async with conn.transaction():
            yield conn
            # Transaction auto-commits if no exception
            # Transaction auto-rolls back if exception occurs
