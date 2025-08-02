# A2A Agent Implementation

This directory contains a complete implementation of an Agent-to-Agent (A2A) protocol compatible agent with clear separation between agent logic and protocol implementation.

## Architecture Overview

### Core Components

1. **Agent Interface** (`interfaces.py`): Defines the abstract interfaces for agents, tools, and A2A protocol adapters
2. **LLM Agent** (`agent.py`): Core agent implementation with LLM loop and tool orchestration
3. **A2A Adapter** (`a2a_adapter.py`): Protocol adapter that bridges our Agent interface with the A2A SDK
4. **Example Tools** (`example_tools.py`): Sample tool implementations (calculator, text processing, time, storage)
5. **Example Server** (`example_server.py`): Complete example showing how to run an A2A agent server

### Key Design Principles

- **Separation of Concerns**: Agent logic is independent of A2A protocol details
- **Pluggable Architecture**: Tools and LLM clients can be easily swapped
- **Testing Support**: Mock adapters allow development without A2A SDK
- **Clear Interfaces**: Well-defined abstractions for all components

## Quick Start

### 1. Install Dependencies

For mock testing (no A2A SDK required):
```bash
# No additional dependencies needed for mock testing
```

For real A2A integration:
```bash
uv add a2a-sdk
```

### 2. Run the Example

```bash
# Run with mock adapter (for testing)
uv run src/buddy/a2a_agent/example_server.py

# Run with real A2A SDK
uv run src/buddy/a2a_agent/example_server.py --no-mock
```

### 3. Test the Implementation

```bash
uv run test_a2a_agent.py
```

## Using with A2A Inspector

1. **Start the A2A Inspector**:
   ```bash
   git clone https://github.com/a2aproject/a2a-inspector.git
   cd a2a-inspector
   uv sync
   cd backend && uv run app.py &
   cd frontend && npm install && npm run build -- --watch
   ```

2. **Start your agent**:
   ```bash
   uv run src/buddy/a2a_agent/example_server.py --no-mock --port 8001
   ```

3. **Connect A2A Inspector to your agent** at `localhost:8001`

## Agent Capabilities

The example agent provides these skills:

### General Skills
- **general_query**: Answer general questions using LLM reasoning
- **tool_execution**: Execute tasks by reasoning about which tools to use

### Tool-Specific Skills
- **use_calculator**: Perform mathematical calculations
- **use_text_processor**: Process and analyze text (word count, case conversion, etc.)
- **use_time_tool**: Get current time and perform time operations
- **use_data_storage**: Store and retrieve data in memory

## Creating Your Own Agent

### 1. Implement Tools

```python
from src.buddy.a2a_agent import Tool

class MyCustomTool(Tool):
    def get_name(self) -> str:
        return "my_tool"

    def get_description(self) -> str:
        return "Description of what my tool does"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param1"]
        }

    async def execute(self, parameters: Dict[str, Any]) -> Any:
        # Tool implementation
        return {"result": "tool output"}
```

### 2. Create Your Agent

```python
from src.buddy.a2a_agent import LLMAgent, create_a2a_adapter

# Create tools
tools = [MyCustomTool()]

# Create agent
agent = LLMAgent(
    name="MyAgent",
    description="My custom A2A agent",
    tools=tools,
    llm_client=my_llm_client  # Your LLM client
)

# Create A2A adapter
adapter = create_a2a_adapter(agent, use_mock=False)

# Start server
adapter.start_server("localhost", 8000)
```

### 3. Integrate with Real LLM

Replace the `MockLLMClient` with your actual LLM integration:

```python
from src.buddy.llm.llm import LLMClient  # Use your existing LLM client

class YourLLMClient:
    async def generate_response(self, prompt: str) -> str:
        # Your LLM integration here
        response = await your_llm_api.generate(prompt)
        return response
```

## Testing Without A2A SDK

The implementation includes a `MockA2AServerAdapter` that allows you to:

1. **Test agent logic** without installing the A2A SDK
2. **Simulate A2A requests** for development
3. **Debug agent behavior** in isolation

```python
# Create mock adapter
adapter = create_a2a_adapter(agent, use_mock=True)
adapter.start_server("localhost", 8000)

# Simulate A2A requests
result = await adapter.simulate_request(
    skill_name="use_calculator",
    parameters={"expression": "2 + 2"}
)
```

## Integration Points

### For A2A Protocol
- `A2AServerAdapter`: Bridges to real A2A SDK
- Handles capability discovery and skill execution
- Manages A2A protocol communication

### For Agent Logic
- `Agent` interface: Define what your agent can do
- `Tool` interface: Define what tools your agent has
- `LLMAgent`: Orchestrates LLM reasoning and tool usage

### For Testing
- `MockA2AServerAdapter`: Test without A2A SDK
- Mock LLM clients for unit testing
- Comprehensive test suite in `test_a2a_agent.py`

## Next Steps

1. **Replace Mock LLM**: Integrate with your actual LLM client
2. **Add Real Tools**: Implement tools specific to your use case
3. **Install A2A SDK**: For production deployment
4. **Deploy and Test**: Use A2A Inspector to validate your agent

The architecture is designed to make each of these steps independent and straightforward.
