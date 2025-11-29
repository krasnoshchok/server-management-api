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

router = APIRouter(
    prefix="/servers",
    tags=["servers"]
)


@router.get("/", response_model=List[ServerResponse])
def get_all_servers():
    """
    Retrieve all servers from the database.

    Returns a list of all servers with their configurations and datacenter assignments.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, hostname, configuration, datacenter_id, 
                       created_at, modified_at
                FROM public.server
                ORDER BY id
            """)
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
            cur.execute("""
                SELECT id, hostname, configuration, datacenter_id,
                       created_at, modified_at
                FROM public.server
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
            cur.execute("SELECT id FROM public.datacenter WHERE id = %s",
                        (server.datacenter_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Datacenter with id {server.datacenter_id} does not exist"
                )

            # Insert server
            cur.execute("""
                INSERT INTO public.server (hostname, configuration, datacenter_id)
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
    """
    Update an existing server.

    - **server_id**: ID of the server to update
    - All fields are optional, only provided fields will be updated
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if server exists
            cur.execute("SELECT id FROM public.server WHERE id = %s", (server_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Server with id {server_id} not found"
                )

            # Build dynamic update query
            update_fields = []
            params = []

            if server.hostname is not None:
                update_fields.append("hostname = %s")
                params.append(server.hostname)

            if server.configuration is not None:
                update_fields.append("configuration = %s")
                params.append(psycopg2.extras.Json(server.configuration))

            if server.datacenter_id is not None:
                # Check if datacenter exists
                cur.execute("SELECT id FROM public.datacenter WHERE id = %s",
                            (server.datacenter_id,))
                if not cur.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Datacenter with id {server.datacenter_id} does not exist"
                    )
                update_fields.append("datacenter_id = %s")
                params.append(server.datacenter_id)

            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )

            update_fields.append("modified_at = NOW()")
            params.append(server_id)

            query = f"""
                UPDATE public.server
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, hostname, configuration, datacenter_id,
                          created_at, modified_at
            """

            cur.execute(query, params)
            updated_server = cur.fetchone()
            return updated_server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: int):
    """
    Delete a server by ID.

    - **server_id**: ID of the server to delete
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if server exists
            cur.execute("SELECT id FROM public.server WHERE id = %s", (server_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Server with id {server_id} not found"
                )

            # Delete server
            cur.execute("DELETE FROM public.server WHERE id = %s", (server_id,))
