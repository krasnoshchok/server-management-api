"""
API endpoints for managing server resources.

This router provides CRUD operations for servers, allowing retrieval,
creation, updating, and deletion of individual server records within a
PostgreSQL database, handling connections via `app.database.get_db_connection`.

The operations include:
- GET /servers: Retrieve a list of all servers.
- GET /servers/{server_id}: Retrieve a specific server by its ID.
- POST /servers: Create a new server, associating it with an existing datacenter.
- PUT /servers/{server_id}: Update the details of an existing server.
- DELETE /servers/{server_id}: Delete a server by its ID.

Data models used:
- ServerUpdate: Model for updating an existing server (all fields optional).
- ServerResponse: Model for the server data returned by the API.

Dependencies:
- fastapi: Core framework for defining the API routes.
- psycopg2.extras: Used for serializing JSON data (`psycopg2.extras.Json`) into the database.
- app.database: Provides the database connection utility (`get_db_connection`).
- app.models: Defines the data structures for server requests and responses.
"""
from typing import List
from fastapi import APIRouter, HTTPException, status
import psycopg2.extras

from app.database import get_db_connection
from app.models import ServerBase, ServerUpdate, ServerResponse
from app.constants import TABLE_SERVER, TABLE_DATACENTER, TABLE_SWITCH_TO_SERVER

router = APIRouter(
    prefix="/servers",
    tags=["servers"]
)


@router.get("/", response_model=List[ServerResponse])
def get_all_servers(skip: int = 0, limit: int = 100):
    """
    Retrieve servers from the database with pagination.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)

    Returns a paginated list of servers.
    """
    # Validate limit to prevent abuse
    limit = min(limit, 1000)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, hostname, configuration, datacenter_id, 
                       created_at, modified_at
                FROM {TABLE_SERVER}
                ORDER BY id
                LIMIT %s OFFSET %s
            """, (limit, skip))
            servers = cur.fetchall()
            return servers


@router.get("/{server_id}", response_model=ServerResponse)
def get_server(server_id: int):
    """
    Retrieve a single server by ID.

    - **server_id**: The ID of the server to retrieve
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, hostname, configuration, datacenter_id,
                       created_at, modified_at
                FROM {TABLE_SERVER}
                WHERE id = %s
            """, (server_id,))
            server = cur.fetchone()

            if not server:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Server with id {server_id} not found"
                )

            return server


@router.post("/", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
def create_server(server: ServerBase):
    """
    Add a new server to a datacenter.

    - **hostname**: Server hostname (required)
    - **configuration**: JSON configuration object (optional)
    - **datacenter_id**: ID of the datacenter (required)
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if datacenter exists
            cur.execute(f"SELECT id FROM {TABLE_DATACENTER} WHERE id = %s",
                        (server.datacenter_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Datacenter with id {server.datacenter_id} does not exist"
                )

            # Insert server
            cur.execute(f"""
                INSERT INTO {TABLE_SERVER} (hostname, configuration, datacenter_id)
                VALUES (%s, %s, %s)
                RETURNING id, hostname, configuration, datacenter_id, 
                          created_at, modified_at
            """, (
                server.hostname,
                psycopg2.extras.Json(server.configuration),
                server.datacenter_id
            ))

            new_server = cur.fetchone()
            return new_server


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(server_id: int, server: ServerUpdate):
    """Update an existing server."""

    # Define allowed fields with their column names
    allowed_fields = {
        'hostname': 'hostname',
        'configuration': 'configuration',
        'datacenter_id': 'datacenter_id'
    }

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Build update fields and params
            update_fields = []
            params = []

            # Get only the fields that were provided (not None)
            update_data = server.model_dump(exclude_unset=True)

            for field_name, value in update_data.items():
                if field_name in allowed_fields:
                    column_name = allowed_fields[field_name]

                    # Special handling for datacenter_id validation
                    if field_name == 'datacenter_id':
                        cur.execute(
                            f"SELECT id FROM {TABLE_DATACENTER} WHERE id = %s",
                            (value,)
                        )
                        if not cur.fetchone():
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Datacenter with id {value} does not exist"
                            )

                    # Special handling for configuration JSON
                    if field_name == 'configuration':
                        value = psycopg2.extras.Json(value)

                    update_fields.append(f"{column_name} = %s")
                    params.append(value)

            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )

            # Add modified timestamp and server_id
            update_fields.append("modified_at = NOW()")
            params.append(server_id)

            # Now it's safe because we've validated all column names
            query = f"""
                UPDATE {TABLE_SERVER}
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, hostname, configuration, datacenter_id,
                          created_at, modified_at
            """

            cur.execute(query, params)
            updated_server = cur.fetchone()

            if not updated_server:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Server with id {server_id} not found"
                )

            return updated_server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: int):
    """
    Delete a server by ID.

    This will also delete all switch associations for this server.

    - **server_id**: ID of the server to delete
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if server exists
            cur.execute(
                f"SELECT id FROM {TABLE_SERVER} WHERE id = %s",
                (server_id,)
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Server with id {server_id} not found"
                )

            # First, delete all switch-to-server associations
            cur.execute(
                f"DELETE FROM {TABLE_SWITCH_TO_SERVER} WHERE server_id = %s",
                (server_id,)
            )

            # Then delete the server itself
            cur.execute(
                f"DELETE FROM {TABLE_SERVER} WHERE id = %s",
                (server_id,)
            )
