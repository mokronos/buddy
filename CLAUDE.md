# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Buddy is an autonomous LLM agent with comprehensive system tools. It provides a command-line interface to interact with large language models enhanced with powerful tools including a planner/notetaking application, Model Context Protocol (MCP) installer/manager, and code interpreter/Python REPL. The goal is to build a JARVIS-like assistant with self-improvement capabilities.

## Development Environment

- **Python Version**: Requires Python 3.13+
- **Package Manager**: Use `uv` for all project operations instead of pip
- **Virtual Environment**: Managed via `uv sync`

## Common Commands

### Running the Application
```bash
uv run src/buddy/main.py
```

### Development Setup
```bash
# Install environment and pre-commit hooks
make install

# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Code Quality & Testing
```bash
# Run all code quality checks (linting, type checking, dependency analysis)
make check

# Run tests with coverage
make test
# Or directly: uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=xml

# Run pre-commit hooks
make pre-commit
# Or: uv run pre-commit run -a

# Type checking
uv run mypy

# Linting and formatting
uv run ruff check
uv run ruff format
```

### Documentation
```bash
# Build and serve docs
make docs

# Test documentation build
make docs-test
```

### Build & Distribution
```bash
# Build wheel file
make build

# Clean build artifacts
make clean-build
```

## Architecture Overview

The project consists of four main components that work together to provide an autonomous LLM agent system accessible via the Agent-to-Agent (A2A) protocol:

### 1. Agent Loop
The core agent loop implements a continuous interaction cycle between an LLM and its environment:

- **LLM Interaction**: Uses LiteLLM for multi-provider support (default: `gemini/gemini-2.5-flash-preview-04-17`)
- **Tool Integration**: The LLM can call available tools based on their auto-generated schemas
- **Environment Feedback**: Tools return results that inform the next LLM iteration
- **Human-in-the-Loop**: Supports human interrupts and input to guide the agent
- **State Management**: Maintains conversation state and context across iterations
- **Context Management**: Manages the size and content of context sent to the LLM on each request:
  - **Context Window Limits**: Respects model-specific token limits to prevent truncation errors
  - **Message Prioritization**: Keeps recent messages and important system prompts while dropping older content
  - **Context Compression**: Summarizes or compresses older conversation history when needed
  - **Tool Result Filtering**: Manages large tool outputs to fit within context constraints
  - **Dynamic Context Sizing**: Adjusts context size based on current task complexity and available tokens
  - **Context Awareness**: Tracks token usage and provides feedback when approaching limits
- **Streaming Support**: Real-time response streaming for better user experience
- **Checkpointing**: Conversation persistence using LangGraph's InMemorySaver

The loop continues until the LLM determines the task is complete or human intervention is required.

### 2. A2A Server Wrapper
An Agent-to-Agent (A2A) protocol server that wraps the core agent and exposes it as a standardized agent service:

- **A2A Protocol Implementation**: Full compliance with Google's Agent-to-Agent protocol specification
- **Agent Interface**: Exposes the core agent capabilities through standardized A2A endpoints
- **Session Management**: Handles multiple concurrent A2A client sessions
- **Event System**: Implements A2A event callbacks for:
  - Agent lifecycle events (start, stop, pause, resume)
  - Tool execution notifications
  - Status updates and progress reporting
- **Push Notifications**: Real-time updates to connected A2A clients about agent state changes
- **Capability Discovery**: Advertises agent skills and available tools to A2A clients
- **Authentication & Authorization**: Manages A2A client access and permissions
- **Message Translation**: Converts between internal agent state and A2A protocol messages
- **WebSocket/HTTP Support**: Supports both real-time and request-response A2A interactions

This layer enables any A2A-compatible client to interact with the agent, making frontends interchangeable.

### 3. CLI Frontend (A2A Client)
A command-line interface that connects to the agent via the A2A protocol:

- **A2A Client Implementation**: Connects to the local A2A server as a standard A2A client
- **Interactive Session**: Provides a conversational interface through A2A protocol messages
- **Command Handling**: Translates user input into A2A protocol requests
- **Output Formatting**: Displays agent responses received via A2A protocol in a readable format
- **Real-time Updates**: Receives and displays streaming responses and push notifications from A2A server
- **Session Management**: Handles A2A session initialization and cleanup

Located in `src/buddy/cli/` with the main entry point at `src/buddy/main.py`. This design allows easy addition of other frontends (web UI, mobile app, IDE plugins) that can all connect as A2A clients.

### 4. Tool Base Class System
A flexible framework for extending agent capabilities through tools:

- **Abstract Base Class**: `Tool` class in `src/buddy/tools/tool.py` defines the interface
- **Schema Auto-generation**: Tools automatically generate OpenAI-compatible schemas from type hints
- **Type Safety**: Enforces proper typing for tool inputs and outputs
- **Easy Extension**: New tools inherit from the base class and implement the `run` method
- **Tool Discovery**: Tools are automatically integrated into the agent's capabilities
- **Error Handling**: Consistent error handling and response patterns across all tools

Tool implementations are located in `src/buddy/tools/` with each tool as a separate module.

### Directory Structure

- `src/buddy/` - Main package
  - `agent/` - Core agent implementation
    - `loop.py` - Main agent loop logic
    - `state.py` - State management and context handling
    - `interfaces.py` - Agent interface definitions
  - `a2a/` - Agent-to-Agent protocol implementation
    - `server.py` - A2A server that wraps the core agent
    - `protocol.py` - A2A protocol message handling
    - `events.py` - Event system and callbacks
    - `client.py` - A2A client base implementation
  - `cli/` - CLI frontend (A2A client)
    - `client.py` - CLI A2A client implementation
    - `interface.py` - User interface and formatting
    - `commands.py` - Command parsing and handling
  - `tools/` - Tool implementations
    - `tool.py` - Abstract base class for tools
    - `*.py` - Individual tool implementations
  - `llm/` - LLM integration and utilities
    - `llm.py` - LiteLLM integration
    - `context.py` - Context management and token handling
  - `main.py` - Application entry point
- `tests/` - Test suite
  - `test_agent/` - Agent loop tests
  - `test_a2a/` - A2A protocol tests
  - `test_cli/` - CLI client tests
  - `test_tools/` - Tool tests
- `docs/` - Documentation source

## Development Conventions

- Use `uv run <file>` instead of `python <file>`
- Use `uv add <package>` instead of `pip install <package>`
- Write self-explanatory code with minimal comments
- Add tests for each implemented feature using `uv run pytest`
- Place code files in the library folder (`buddy`) or subfolders
- Follow the existing code style and patterns
- **IMPORTANT**: Always use absolute imports, never relative imports
  - ✅ Correct: `from buddy.tools.tool import Tool`
  - ✅ Correct: `from buddy.agent.interfaces import Agent`
  - ❌ Wrong: `from .tool import Tool`
  - ❌ Wrong: `from ..tools.tool import Tool`
- **Commit Message Style**: Keep commit messages concise and descriptive
  - ✅ Correct: `refactor: convert to absolute imports and reorganize agent module`
  - ❌ Wrong: Adding co-authorship or listing all changes in commit message
  - ❌ Wrong: Multi-line commit messages with detailed bullet points
- Use `git add -A` instead of `git add .` to stage all changes
- Dont use `Optional[]` for optional arguments, use `| None` instead

## Tool Development

When creating new tools:
1. Inherit from the abstract `Tool` class
2. Implement the `run` method with proper type hints
3. The schema will be auto-generated from method signatures
4. Tools are integrated into the graph's `ToolNode`

## Configuration

- Uses environment variables loaded via `python-dotenv`
- Model configuration supports multiple providers through LiteLLM
- Default model: `gemini/gemini-2.5-flash-preview-04-17`
- Checkpointing enabled for conversation persistence
