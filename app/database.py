"""
Database connection utility module.

This module provides a context manager, `get_db_connection`, for safely
establishing and managing connections to a PostgreSQL database using `psycopg2`.

Configuration:
- Database credentials are loaded from environment variables using `dotenv`.
- Environment variables expected:
    - DB_HOST (default: localhost)
    - DB_NAME (default: server_management)
    - DB_USER (default: postgres)
    - DB_PASSWORD (default: postgres)
    - DB_PORT (default: 5432)

Features:
- **Automatic Connection Handling**: The context manager ensures the connection
  is always closed upon exiting the `with` block.
- **Transaction Management**:
    - A transaction is **committed** upon successful execution within the `with` block.
    - A transaction is **rolled back** if any exception occurs.
- **Dictionary Cursor**: Uses `psycopg2.extras.RealDictCursor` so that
  database query results are returned as dictionaries instead of tuples.
"""
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "server_management"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "port": os.getenv("DB_PORT", "5432")
}


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
