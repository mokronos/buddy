from pydantic import BaseModel
from buddy.tools.tool import Tool

class MCPTool(BaseModel):
    name: str
    command: str
    args: list[str]

class State(BaseModel):
    mcps: list[MCPTool]
    cores: list[Tool]
    messages: list[dict]
