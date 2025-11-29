"""
Pydantic models for representing and validating Server data in the API.

These models define the structure for data transferred between the API clients
and the server for server-related operations (Create, Update, and Response).

Models:
- ServerBase: Contains the core fields common to all server representations.
- ServerUpdate: Used for validating data when updating an existing server (all fields are optional).
- ServerResponse: Used for structuring the data returned by the API after a server operation,
  including read-only fields like ID and timestamps.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ServerBase(BaseModel):
    """Base server model with common fields"""
    hostname: str = Field(..., description="Server hostname", example="myserver.local.lan")
    configuration: Dict[str, Any] = Field(default_factory=dict,
                                          description="Server configuration as JSON")
    datacenter_id: int = Field(..., description="ID of the datacenter", example=1)


class ServerUpdate(BaseModel):
    """Model for updating a server (all fields optional)"""
    hostname: Optional[str] = Field(None, example="updated-server.local.lan")
    configuration: Optional[Dict[str, Any]] = None
    datacenter_id: Optional[int] = None


# pylint: disable=R0903
class ServerResponse(ServerBase):
    """Model for server responses"""
    id: int
    created_at: datetime
    modified_at: datetime

    class Config:
        """Pydantic configuration class."""
        from_attributes = True
