from litellm import get_supported_openai_params, supports_function_calling
from buddy.llm import call_llm


# model = "openrouter/meta-llama/llama-4-maverick:free"
model = "openrouter/meta-llama/llama-3.3-70b-instruct:free"
# model = "openrouter/deepseek/deepseek-r1-zero:free"
# model = "openrouter/deepseek/deepseek-chat-v3-0324:free"
# model = "github/gpt-4o-mini"

print(supports_function_calling(model))

exit()

resp = get_supported_openai_params(model=model)

print(resp)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "useful for when you need to answer questions about current events",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The input query for searching",
                    }
                },
            },
        },
    }
]

system_prompt = "You are a helpful assistant."

resp = call_llm(
    model,
    [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": "What is the capital of France?",
        },
    ],
    tools=tools,
    tool_choice={"type": "function", "function": {"name": "search"}},
)

print(resp)
