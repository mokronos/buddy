"""OpenAI Codex model configuration for special endpoints."""

import os
from typing import cast

from openai import AsyncOpenAI
from pydantic_ai import ModelSettings
from pydantic_ai.models.openai import OpenAIModelName, OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider


def create_codex_model(
    model_name: str,
    api_key: str | None = None,
    account_id: str | None = None,
) -> OpenAIResponsesModel:
    """Create an OpenAI model configured for the Codex endpoint.

    Args:
        model_name: The model name to use (e.g., "gpt-5.2", "gpt-5.3")
        api_key: OpenAI access token (defaults to OPENAI_ACCESS_TOKEN env var)
        account_id: ChatGPT account ID (defaults to ACCOUNT_ID env var)

    Returns:
        Configured OpenAIResponsesModel instance
    """
    default_headers = {
        "originator": "opencode",
        "Openai-Intent": "conversation-edits",
        "User-Agent": "opencode/0.0.0",
    }

    if account_id or (account_id := os.getenv("ACCOUNT_ID")):
        default_headers["ChatGPT-Account-Id"] = account_id

    openai_client = AsyncOpenAI(
        api_key=api_key or os.getenv("OPENAI_ACCESS_TOKEN"),
        base_url="https://chatgpt.com/backend-api/codex",
        default_headers=default_headers,
    )

    casted_model_name: OpenAIModelName = cast(OpenAIModelName, model_name)
    return OpenAIResponsesModel(
        casted_model_name,
        provider=OpenAIProvider(openai_client=openai_client),
        settings=cast(ModelSettings, {"openai_store": False}),
    )
