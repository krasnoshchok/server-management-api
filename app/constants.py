"""
Database constants and configuration.
"""

# Table names with schema
TABLE_SERVER = "public.server"
TABLE_DATACENTER = "public.datacenter"
TABLE_SWITCH = "public.switch"
TABLE_SWITCH_TO_SERVER = "public.switch_to_server"

# Or if you want more flexibility:
SCHEMA = "public"


def table(name: str) -> str:
    """Get fully qualified table name."""
    return f"{SCHEMA}.{name}"
