import tiktoken
from buddy.model import get_model, get_oai_model
from langchain_core.messages import SystemMessage


encoding = tiktoken.encoding_for_model("gpt-4o")

system_msg = SystemMessage(content=".")

msg = "Hello" * 10
total_tokens = len(encoding.encode(msg))

print(total_tokens)

llm = get_model()
print(llm.invoke([system_msg, {"role": "user", "content": msg}]))

llm_oai = get_oai_model()

completion = llm_oai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Hello"
        },
        {
            "role": "user",
            "content": msg,
        },
    ],
)

print(completion)
print(completion.usage)
