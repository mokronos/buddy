import uuid

from fasta2a.client import A2AClient
from fasta2a.schema import Message, TextPart

client = A2AClient(base_url="http://localhost:8000")


async def main():
    part = TextPart(text="Hello, world!", kind="text")

    msg = Message(
        role="user",
        parts=[part],
        kind="message",
        task_id=str(uuid.uuid4()),
        context_id=str(uuid.uuid4()),
        message_id=str(uuid.uuid4()),
    )

    res = await client.send_message(msg)

    print(res)
    print()

    task_id = res["result"]["history"][0]["task_id"]

    res = await client.get_task(task_id)
    print(res)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
