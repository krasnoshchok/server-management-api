"""
API endpoints for managing server resources (Async Version).

This router provides async CRUD operations for servers.
All database queries are now non-blocking for better concurrency.

Key differences from sync version:
- All functions are async (async def)
- Database queries use asyncpg syntax
- Results are returned as lists of dicts (asyncpg.Record objects)
"""
import logging
import json
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from app.database import get_db_connection
from app.models import ServerBase, ServerUpdate, ServerResponse
from app.constants import TABLE_SERVER, TABLE_DATACENTER, TABLE_SWITCH_TO_SERVER

router = APIRouter(
    prefix="/servers",
    tags=["servers"]
)

logger = logging.getLogger(__name__)


def serialize_server(server) -> dict:
    """Convert asyncpg Record to JSON-serializable dict."""
    server_dict = dict(server)

    # Handle datetime objects
    if isinstance(server_dict.get('created_at'), datetime):
        server_dict['created_at'] = server_dict['created_at'].isoformat()
    if isinstance(server_dict.get('modified_at'), datetime):
        server_dict['modified_at'] = server_dict['modified_at'].isoformat()

    # Ensure configuration is a dict (asyncpg should handle this automatically)
    if isinstance(server_dict.get('configuration'), str):
        server_dict['configuration'] = json.loads(server_dict['configuration'])

    # If configuration is None or empty, use empty dict
    if not server_dict.get('configuration'):
        server_dict['configuration'] = {}

    return server_dict


@router.get("/", response_model=List[ServerResponse])
async def get_all_servers(skip: int = 0, limit: int = 100):
    """
    Retrieve servers from the database with pagination (Async).

    Now multiple requests can run concurrently without blocking!
    """
    limit = min(limit, 1000)

    logger.info("Fetching servers with skip=%s, limit=%s", skip, limit)

    async with get_db_connection() as conn:
        # asyncpg uses $1, $2 for parameters instead of %s
        servers = await conn.fetch(f"""
            SELECT id, hostname, configuration, datacenter_id, 
                   created_at, modified_at
            FROM {TABLE_SERVER}
            ORDER BY id
            LIMIT $1 OFFSET $2
        """, limit, skip)

        logger.info("Retrieved %s servers", len(servers))

        return [serialize_server(server) for server in servers]


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(server_id: int):
    """
    Retrieve a single server by ID (Async).
    """
    logger.info("Fetching server with id=%s", server_id)

    async with get_db_connection() as conn:
        # fetchrow returns a single row or None
        server = await conn.fetchrow(f"""
            SELECT id, hostname, configuration, datacenter_id,
                   created_at, modified_at
            FROM {TABLE_SERVER}
            WHERE id = $1
        """, server_id)

        if not server:
            logger.warning("Server with id=%s not found", server_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {server_id} not found"
            )

        logger.info("Retrieved server: %s (id=%s)", server['hostname'], server_id)
        return serialize_server(server)


@router.post("/", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(server: ServerBase):
    """
    Add a new server to a datacenter (Async).
    """
    logger.info("Creating server: hostname=%s, datacenter_id=%s",
                server.hostname, server.datacenter_id)

    async with get_db_connection() as conn:
        # Check if datacenter exists
        datacenter = await conn.fetchrow(
            f"SELECT id FROM {TABLE_DATACENTER} WHERE id = $1",
            server.datacenter_id
        )

        if not datacenter:
            logger.error("Datacenter with id=%s does not exist", server.datacenter_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Datacenter with id {server.datacenter_id} does not exist"
            )

        # Convert Pydantic model to dict for storage
        config_dict = server.configuration.model_dump(exclude_none=True)

        # Insert server - asyncpg needs JSON as string with ::jsonb cast
        new_server = await conn.fetchrow(f"""
            INSERT INTO {TABLE_SERVER} (hostname, configuration, datacenter_id)
            VALUES ($1, $2::jsonb, $3)
            RETURNING id, hostname, configuration, datacenter_id, 
                      created_at, modified_at
        """, server.hostname, json.dumps(config_dict), server.datacenter_id)

        logger.info("Created server with id=%s, hostname=%s",
                    new_server['id'], new_server['hostname'])

        return serialize_server(new_server)


@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(server_id: int, server: ServerUpdate):
    """
    Update an existing server (Async).
    """
    logger.info("Updating server id=%s", server_id)

    allowed_fields = {
        'hostname': 'hostname',
        'configuration': 'configuration',
        'datacenter_id': 'datacenter_id'
    }

    async with get_db_connection() as conn:
        # Build update fields and params
        update_fields = []
        params = []
        param_index = 1

        update_data = server.model_dump(exclude_unset=True)
        logger.debug("Update data for server id=%s: %s", server_id, update_data)

        for field_name, value in update_data.items():
            if field_name in allowed_fields:
                column_name = allowed_fields[field_name]

                # Special handling for datacenter_id validation
                if field_name == 'datacenter_id':
                    datacenter = await conn.fetchrow(
                        f"SELECT id FROM {TABLE_DATACENTER} WHERE id = $1",
                        value
                    )
                    if not datacenter:
                        logger.error("Datacenter with id=%s does not exist", value)
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Datacenter with id {value} does not exist"
                        )
                    update_fields.append(f"{column_name} = ${param_index}")
                    params.append(value)
                    param_index += 1

                # Special handling for configuration JSONB
                elif field_name == 'configuration':
                    if hasattr(value, 'model_dump'):
                        value = value.model_dump(exclude_none=True)
                    # For JSONB columns, cast to jsonb and pass as JSON string
                    update_fields.append(f"{column_name} = ${param_index}::jsonb")
                    params.append(json.dumps(value))
                    param_index += 1
                    logger.debug("Configuration value to store: %s", json.dumps(value))

                # Normal fields
                else:
                    update_fields.append(f"{column_name} = ${param_index}")
                    params.append(value)
                    param_index += 1

        if not update_fields:
            logger.warning("No fields to update for server id=%s", server_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Add modified timestamp and server_id
        update_fields.append("modified_at = NOW()")
        params.append(server_id)

        query = f"""
            UPDATE {TABLE_SERVER}
            SET {', '.join(update_fields)}
            WHERE id = ${param_index}
            RETURNING id, hostname, configuration, datacenter_id,
                      created_at, modified_at
        """

        logger.debug("Executing query: %s with params: %s", query, params)

        updated_server = await conn.fetchrow(query, *params)

        if not updated_server:
            logger.warning("Server with id=%s not found for update", server_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {server_id} not found"
            )

        logger.info("Updated server id=%s, hostname=%s",
                    updated_server['id'], updated_server['hostname'])
        return serialize_server(updated_server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(server_id: int):
    """
    Delete a server by ID (Async).
    This will also delete all switch associations for this server.
    """
    logger.info("Deleting server id=%s", server_id)

    async with get_db_connection() as conn:
        # Delete associations first
        association_result = await conn.execute(
            f"DELETE FROM {TABLE_SWITCH_TO_SERVER} WHERE server_id = $1",
            server_id
        )

        # execute() returns "DELETE N" where N is the row count
        association_count = int(association_result.split()[-1])

        if association_count > 0:
            logger.info("Deleted %s switch associations for server id=%s",
                        association_count, server_id)

        # Delete the server
        delete_result = await conn.execute(
            f"DELETE FROM {TABLE_SERVER} WHERE id = $1",
            server_id
        )

        deleted_count = int(delete_result.split()[-1])

        if deleted_count == 0:
            logger.warning("Server with id=%s not found for deletion", server_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {server_id} not found"
            )

        logger.info("Deleted server id=%s", server_id)
