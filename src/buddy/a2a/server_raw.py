from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, Part, TaskState, TextPart
from a2a.utils import new_task
from dotenv import load_dotenv
from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    TextPartDelta,
    ToolCallPart,
    ToolCallPartDelta,
)
from pydantic_ai.toolsets import FunctionToolset

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


agent_card = AgentCard(
    name="Test Agent",
    description="Test Agent",
    url="http://localhost:8000",
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
        task = context.current_task or new_task(context.message)

        updater = TaskUpdater(event_queue, task.id, context.context_id)

        await event_queue.enqueue_event(task)

        await updater.update_status(TaskState.working)

        output = "Agent didn't produce any output"
        res = None

        async for event in agent.run_stream_events(query):
            pprint(event)

            if isinstance(event, PartStartEvent):
                part = event.part
                if isinstance(part, TextPart):
                    await updater.add_artifact(
                        [Part(root=TextPart(text=part.text))],
                        name="start",
                    )
                if isinstance(part, ToolCallPart):
                    await updater.add_artifact(
                        [Part(root=TextPart(text=part.tool_name))],
                        name="start_tool",
                    )
                    await updater.add_artifact(
                        [Part(root=TextPart(text=str(part.args)))],
                        name="start_tool",
                    )
            if isinstance(event, PartDeltaEvent):
                delta = event.delta

                if isinstance(delta, TextPartDelta):
                    await updater.add_artifact(
                        [Part(root=TextPart(text=delta.content_delta))],
                        name="delta",
                        append=True,
                    )

                if isinstance(delta, ToolCallPartDelta):
                    if delta.tool_name_delta:
                        await updater.add_artifact(
                            [Part(root=TextPart(text=delta.tool_name_delta))],
                            name="delta_tool",
                            append=True,
                        )
                    if delta.args_delta:
                        await updater.add_artifact(
                            [Part(root=TextPart(text=str(delta.args_delta)))],
                            name="delta_tool",
                            append=True,
                        )

            # end just repeats the whole part (probably should still send, for easier handling on client, but different artifact)
            if isinstance(event, PartEndEvent):
                part = event.part
                if isinstance(part, TextPart):
                    await updater.add_artifact(
                        [Part(root=TextPart(text=part.text))],
                        name="end",
                    )
                if isinstance(part, ToolCallPart):
                    await updater.add_artifact(
                        [Part(root=TextPart(text=part.tool_name))],
                        name="end_tool",
                    )
                    await updater.add_artifact(
                        [Part(root=TextPart(text=str(part.args)))],
                        name="end_tool",
                    )

            if isinstance(event, AgentRunResultEvent):
                res = event.result

        if res and res.output:
            output = res.output

        await updater.add_artifact(
            [Part(root=TextPart(text=output))],
            name="output",
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
