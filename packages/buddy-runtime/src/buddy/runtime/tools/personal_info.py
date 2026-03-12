from pydantic_ai import Tool

_PEOPLE_INFO = {
    "basti": "29 years old, works as a data scientist in nuremberg in germany and has a sister named caro.",
    "john": "29 years old, works as a data scientist in nuremberg in germany and has a sister named caro.",
}


def personal_info(name: str) -> str:
    """Retrieve personal information about a person."""
    normalized_name = name.lower().strip()
    if normalized_name in _PEOPLE_INFO:
        return _PEOPLE_INFO[normalized_name]
    return f"No information available for '{name}'"


personal_info_tool = Tool(
    personal_info,
    name="personal_info",
    description="Retrieves personal information about a person by name",
)
