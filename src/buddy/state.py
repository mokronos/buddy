from pydantic import BaseModel
from buddy.tools.tool import Tool
from typing import Annotated

class MCPTool(BaseModel):
    name: str
    command: str
    args: list[str]

class State(BaseModel):
    mcps: list[MCPTool]
    cores: list[str]
    messages: Annotated[list[dict], lambda left, right: left + right]
