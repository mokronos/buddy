import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai import OpenAI

load_dotenv()


def get_model(endpoint="https://models.inference.ai.azure.com", model_name="gpt-4o-mini", token_name="GITHUB_TOKEN"):
    token = os.environ[token_name]
    # token = SecretStr(os.environ["OPENROUTER_API_KEY"])
    # endpoint = "https://openrouter.ai/api/v1"
    # model_name = "DeepSeek-R1"
    # model_name = "mistralai/mistral-small-3.1-24b-instruct:free"

    return ChatOpenAI(base_url=endpoint, api_key=token, model=model_name)


def get_oai_model(endpoint="https://models.inference.ai.azure.com", token_name="GITHUB_TOKEN"):
    token = os.environ[token_name]
    # token = SecretStr(os.environ["OPENROUTER_API_KEY"])
    # endpoint = "https://openrouter.ai/api/v1"
    # model_name = "DeepSeek-R1"
    # model_name = "mistralai/mistral-small-3.1-24b-instruct:free"

    return OpenAI(base_url=endpoint, api_key=token)
