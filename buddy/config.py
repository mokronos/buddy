from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


class Config(BaseModel):
    # API Configuration
    endpoint: str = Field(default="https://models.inference.ai.azure.com")
    model_name: str = Field(default="gpt-4o-mini")
    token: Optional[str] = Field(default=os.getenv("GITHUB_TOKEN"))

    # Shell command restrictions
    allowed_commands: List[str] = Field(default=["ls", "pwd", "date", "curl -O"])
    blocked_patterns: List[str] = Field(default=["rm", "del", ">", "|", "&", "sudo"])

    # Safety settings
    shell_timeout: int = Field(default=10, description="Timeout in seconds")

    @classmethod
    def from_runnable_config(cls, runnable_config: dict) -> "Config":
        """Create Config instance from LangGraph's RunnableConfig by merging:
        - Default config values
        - Any overrides from RunnableConfig's configurable dict
        """
        default = cls()
        configurable = runnable_config.get("configurable", {})

        # Dynamically merge configurable values with defaults
        kwargs = {
            field: configurable.get(field, getattr(default, field))
            for field in cls.model_fields
        }

        return cls(**kwargs)

    def to_runnable_config(self) -> dict:
        """Convert to LangGraph-compatible RunnableConfig"""
        return {
            "configurable": {
                "api_config": {
                    "endpoint": self.endpoint,
                    "model": self.model_name,
                    "token": self.token,
                },
                "safety_config": {
                    "shell_timeout": self.shell_timeout,
                    "blocked_patterns": self.blocked_patterns,
                },
            }
        }
