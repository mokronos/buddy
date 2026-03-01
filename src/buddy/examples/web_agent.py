from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

load_dotenv()


agent = Agent('openrouter:openrouter/free')

todo = []

@agent.tool
async def todoadd(ctx: RunContext, task: str) -> str:
    global todo
    todo.append(task)
    return f'Added task {task}'

@agent.tool
async def todoread(ctx: RunContext) -> str:
    return 'Todo list:\n' + '\n'.join(todo)

app = agent.to_web()
