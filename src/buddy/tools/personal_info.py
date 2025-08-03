from buddy.tools.tool import Tool


class PersonalInfoTool(Tool):
    """Tool to retrieve personal information about people."""

    def __init__(self) -> None:
        super().__init__(name="personal_info", description="Retrieves personal information about a person by name")

    def run(self, name: str) -> str:
        """Retrieve personal information about a person.

        Args:
            name: The name of the person to look up

        Returns:
            Personal information about the person
        """
        # Simple database of personal information
        people_info = {
            "basti": "29 years old, works as a data scientist in nuremberg in germany and has a sister named caro."
        }

        # Convert to lowercase for case-insensitive matching
        normalized_name = name.lower().strip()

        if normalized_name in people_info:
            return people_info[normalized_name]
        else:
            return f"No information available for '{name}'"
