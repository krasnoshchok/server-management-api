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
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ServerConfiguration(BaseModel):
    """Server hardware configuration with validation."""
    cpu_cores: Optional[int] = Field(None, ge=1, le=128, description="CPU cores (1-128)")
    ram_gb: Optional[int] = Field(None, ge=1, le=1024, description="RAM in GB (1-1024)")
    disk_gb: Optional[int] = Field(None, ge=10, le=10000, description="Disk space in GB (10-10000)")

    @field_validator("cpu_cores", mode="after")
    def validate_cpu_cores(cls, v):  # pylint: disable=no-self-argument
        """Validate allowed CPU core counts."""
        if v is not None and v not in [1, 2, 4, 8, 16, 32, 64, 128]:
            raise ValueError("cpu_cores must be one of: 1, 2, 4, 8, 16, 32, 64, 128")
        return v

    @field_validator("ram_gb", mode="after")
    def validate_ram_gb(cls, v):  # pylint: disable=no-self-argument
        """Validate RAM sizes in GB."""
        allowed = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
        if v is not None and v not in allowed:
            raise ValueError(f"ram_gb must be one of: {allowed}")
        return v


class ServerBase(BaseModel):
    """Base server model shared by creation, update, and response models."""
    hostname: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Server hostname",
        example="myserver.local.lan"
    )
    configuration: ServerConfiguration = Field(
        default_factory=ServerConfiguration,
        description="Server configuration as JSON"
    )
    datacenter_id: int = Field(
        ...,
        description="ID of the datacenter",
        example=1
    )


class ServerUpdate(BaseModel):
    """Model for updating a server (all fields optional)."""
    hostname: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        example="updated-server.local.lan"
    )
    configuration: Optional[ServerConfiguration] = None
    datacenter_id: Optional[int] = None


# pylint: disable=R0903
class ServerResponse(ServerBase):
    """Model for server responses."""
    id: int
    created_at: datetime
    modified_at: datetime
