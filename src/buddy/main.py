import asyncio

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Artifact,
    TaskArtifactUpdateEvent,
    TextPart,
)


class HelloWorldAgent:
    """Hello World Agent."""

    async def invoke(self) -> str:
        resp = "hello world"
        for i in range(10):
            print(f"Sending {i} of 10")
            await asyncio.sleep(1)
            return resp


class HelloWorldAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = HelloWorldAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        await self.agent.invoke()

        for i in range(10):
            text_part = TextPart(text=f"hello world {i}")
            artifact = Artifact(
                artifactId="35",
                parts=[text_part],
            )
            chunk = TaskArtifactUpdateEvent(
                artifact=artifact,
                contextId=context.context_id,
                taskId=context.task_id,
                lastChunk=False,
                append=True,
            )
            await event_queue.enqueue_event(chunk)
            await asyncio.sleep(0.2)

        final_part = TextPart(text="Final Hello World")
        final_artifact = Artifact(
            artifactId="35",
            parts=[final_part],
        )
        final_result = TaskArtifactUpdateEvent(
            artifact=final_artifact,
            contextId=context.context_id,
            taskId=context.task_id,
            lastChunk=True,
        )
        await event_queue.enqueue_event(final_result)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "cancel not supported"
        raise NotImplementedError(msg)


skill = AgentSkill(
    id="hello_world",
    name="Returns hello world",
    description="just returns hello world",
    tags=["hello world"],
    examples=["hi", "hello world"],
)

extended_skill = AgentSkill(
    id="super_hello_world",
    name="Returns a SUPER Hello World",
    description="A more enthusiastic greeting, only for authenticated users.",
    tags=["hello world", "super", "extended"],
    examples=["super hi", "give me a super hello"],
)

# This will be the public-facing agent card
public_agent_card = AgentCard(
    name="Hello World Agent",
    description="Just a hello world agent",
    url="http://localhost:9999/",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],  # Only the basic skill for the public card
    supportsAuthenticatedExtendedCard=True,
)

# This will be the authenticated extended agent card
# It includes the additional 'extended_skill'
specific_extended_agent_card = public_agent_card.model_copy(
    update={
        "name": "Hello World Agent - Extended Edition",  # Different name for clarity
        "description": "The full-featured hello world agent for authenticated users.",
        "version": "1.0.1",  # Could even be a different version
        # Capabilities and other fields like url, defaultInputModes, defaultOutputModes,
        # supportsAuthenticatedExtendedCard are inherited from public_agent_card unless specified here.
        "skills": [
            skill,
            extended_skill,
        ],  # Both skills for the extended card
    }
)

request_handler = DefaultRequestHandler(
    agent_executor=HelloWorldAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

server = A2AStarletteApplication(
    agent_card=public_agent_card,
    http_handler=request_handler,
    extended_agent_card=specific_extended_agent_card,
)

app = server.build()

if __name__ == "__main__":
    uvicorn.run(server.build(), host="0.0.0.0", port=9999)
