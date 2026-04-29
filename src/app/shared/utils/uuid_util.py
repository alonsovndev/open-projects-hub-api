from uuid import UUID


def convert_uuid_to_str(uuid_obj):
    """Convert a UUID object to its string representation."""
    return str(uuid_obj) if uuid_obj else None


def convert_str_to_uuid(uuid_str):
    """Convert a string representation of a UUID to a UUID object."""
    try:
        return UUID(uuid_str) if uuid_str else None
    except ValueError as e:
        raise ValueError(f"Invalid UUID format: {uuid_str}") from e
