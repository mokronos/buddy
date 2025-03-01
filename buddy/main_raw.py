from openai import OpenAI, pydantic_function_tool
import os
from dotenv import load_dotenv
from utils import tool, ToolSet
import subprocess
import time

load_dotenv()

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o-mini"
# model_name = "DeepSeek-R1"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

tools = ToolSet()


@tool
def get_current_weather(location: str) -> str:
    """ Get the current weather in a given location. """
    return f"The current weather in {location} is sunny."

@tool
def multiply(x: int, y: int) -> str:
    return str(x * y)


@tool
def subtract(x: int, y: int) -> str:
    return str(x - y)

@tool
def run_shell_command(command: str) -> str:
    """Executes a shell command and returns the output."""
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    return result.stdout.strip()



tools.add(get_current_weather)
tools.add(multiply)
tools.add(subtract)
tools.add(run_shell_command)

messages=[
    {
        "role": "system",
        "content": "You are a helpful assistant.",
    },
    {
        "role": "user",
        # "content": "Whats 8*3851?",
        "content": "What files are in the current directory? even hidden ones",
    }
]

response = client.chat.completions.create(
    messages=messages,
    tools=tools.schemas(),
    model=model_name
)

for m in messages:
    print(m)

while 1:

    response = client.chat.completions.create(
        messages=messages,
        tools=tools.schemas(),
        model=model_name
    )

    if response.choices[0].message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "tool_calls": response.choices[0].message.tool_calls
            }
        )
        print(messages[-1])
        for tool_call in response.choices[0].message.tool_calls:
            msg = tools.get_message(tool_call)
            messages.append(msg)
            print(messages[-1])
    else:
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        print(messages[-1])
        break
