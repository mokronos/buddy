import os

from dotenv import load_dotenv
from litellm import completion

load_dotenv()

os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")
response = completion(
    model="gemini/gemini-2.0-flash",
    messages=[{"role": "user", "content": "whats the capital of france?"}],
)

print(response)
