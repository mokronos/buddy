import os
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, Part, TaskState
from a2a.utils import new_agent_text_message, new_task
from dotenv import load_dotenv
from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    TextPartDelta,
    ToolCallPart,
    TextPart,
)
from pydantic_ai.toolsets import FunctionToolset

from buddy.a2a.utils import simple_text_part

from uuid import uuid4

load_dotenv()

from devtools import pprint


def random_tool1(arg1: str, arg2: str):
    import time

    time.sleep(3)
    return f"Result of random long running tool call with args: {arg1} | {arg2}" * 20


tool_set = FunctionToolset(
    tools=[
        random_tool1,
    ],
)

agent = Agent(
    model="google-gla:gemini-2.5-flash",
    toolsets=[tool_set],
)

port = os.environ.get("PORT", 10001)


agent_card = AgentCard(
    name="Test Agent",
    description="Test Agent",
    url=f"http://localhost:{port}",
    capabilities=AgentCapabilities(
        streaming=True,
    ),
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[],
    version="0.0.1",
)

pprint(agent_card)


class PyAIAgentExecutor(AgentExecutor):
    def __init__(self, agent: Agent):
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:

        query = context.get_user_input()
        print("\n\n\n Recieved new task with query: ", query, "\n")
        task = context.current_task or new_task(context.message)

        updater = TaskUpdater(event_queue, task.id, context.context_id)

        await event_queue.enqueue_event(task)
        await updater.update_status(TaskState.working, message=new_agent_text_message(f"Recieved new task with query: {query}"))

        output = "Agent didn't produce any output"
        res = None
        cur_artifact_id = None

        async for event in agent.run_stream_events(query):
            pprint(event)

            if isinstance(event, PartStartEvent):
                part = event.part
                cur_artifact_id = str(uuid4())
                if isinstance(part, TextPart):
                    await updater.add_artifact(
                        [simple_text_part(part.content)],
                        name="output_start",
                        artifact_id=cur_artifact_id,
                    )
            if isinstance(event, PartDeltaEvent):
                delta = event.delta

                if isinstance(delta, TextPartDelta):
                    await updater.add_artifact(
                        [simple_text_part(delta.content_delta)],
                        name="output_delta",
                        append=True,
                        artifact_id=cur_artifact_id,
                    )


            # end just repeats the whole part (probably should still send, for easier handling on client, but different artifact)
            if isinstance(event, PartEndEvent):
                part = event.part
                if isinstance(part, TextPart):
                    await updater.add_artifact(
                        [simple_text_part(part.content)],
                        name="output_end",
                        artifact_id=cur_artifact_id,
                    )
                if isinstance(part, ToolCallPart):

                    await updater.update_status(TaskState.working, message=new_agent_text_message(f"Calling tool: {part.tool_name} with args: {part.args}"))

            if isinstance(event, AgentRunResultEvent):
                res = event.result

        if res and res.output:
            output = res.output

        await updater.add_artifact(
            [simple_text_part(output)],
            name="full_output",
        )

        await updater.update_status(TaskState.completed)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancellation is not supported yet")


request_handler = DefaultRequestHandler(
    agent_executor=PyAIAgentExecutor(
        agent=agent,
    ),
    task_store=InMemoryTaskStore(),
)

a2a_app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

app = a2a_app.build()
