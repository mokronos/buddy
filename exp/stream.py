from dotenv import load_dotenv
from pydantic_ai import Agent, AgentRunResultEvent, AgentStreamEvent

load_dotenv()

agent = Agent("google-gla:gemini-2.5-flash")
# agent = Agent('ollama:gemma3:270m')

# result_sync = agent.run_sync('What is the capital of Italy?')
# print(result_sync.output)
# > The capital of Italy is Rome.


async def main():
    # result = await agent.run('What is the capital of France?')
    # print(result.output)
    ##> The capital of France is Paris.

    # async with agent.run_stream('What is the capital of the UK?') as response:
    #    async for text in response.stream_text():
    #        print(text)
    #        #> The capital of
    #        #> The capital of the UK is
    #        #> The capital of the UK is London.

    events: list[AgentStreamEvent | AgentRunResultEvent] = []
    async for event in agent.run_stream_events("Tell me a 2 paragraph story about a cat"):
        # events.append(event)
        print(event)
    # print(events)
    """
    [
        PartStartEvent(index=0, part=TextPart(content='The capital of ')),
        FinalResultEvent(tool_name=None, tool_call_id=None),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='Mexico is Mexico ')),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='City.')),
        PartEndEvent(
            index=0, part=TextPart(content='The capital of Mexico is Mexico City.')
        ),
        AgentRunResultEvent(
            result=AgentRunResult(output='The capital of Mexico is Mexico City.')
        ),
    ]
    """


import asyncio

asyncio.run(main())
