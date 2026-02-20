from buddy.a2a.server import create_app
from buddy.agent.agent import agents

app = create_app(agents)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10001)
