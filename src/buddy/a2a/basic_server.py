import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fasta2a import FastA2A, Worker
from fasta2a.broker import InMemoryBroker
from fasta2a.schema import Artifact, Message, TaskIdParams, TaskSendParams, TextPart
from fasta2a.storage import InMemoryStorage

Context = list[Message]
"""The shape of the context you store in the storage."""


class InMemoryWorker(Worker[Context]):
    async def run_task(self, params: TaskSendParams) -> None:
        task = await self.storage.load_task(params["id"])
        assert task is not None

        await self.storage.update_task(task["id"], state="working")

        context = await self.storage.load_context(task["context_id"]) or []
        context.extend(task.get("history", []))

        # Call your agent here...
        message = Message(
            role="agent",
            parts=[TextPart(text=f"Your context is {len(context) + 1} messages long.", kind="text")],
            kind="message",
            message_id=str(uuid.uuid4()),
        )

        # Update the new message to the context.
        context.append(message)

        artifacts = self.build_artifacts(123)
        await self.storage.update_context(task["context_id"], context)
        await self.storage.update_task(task["id"], state="completed", new_messages=[message], new_artifacts=artifacts)

    async def cancel_task(self, params: TaskIdParams) -> None: ...

    def build_message_history(self, history: list[Message]) -> list[Any]: ...

    def build_artifacts(self, result: Any) -> list[Artifact]: ...


storage = InMemoryStorage()
broker = InMemoryBroker()
worker = InMemoryWorker(storage=storage, broker=broker)


@asynccontextmanager
async def lifespan(app: FastA2A) -> AsyncIterator[None]:
    async with app.task_manager, worker.run():
        yield


app = FastA2A(storage=storage, broker=broker, lifespan=lifespan)
