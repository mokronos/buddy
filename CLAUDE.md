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

### Core Components

- **State Management**: `src/buddy/state.py` - Defines the main State model with MCPTool, cores, and messages
- **Graph-based Architecture**: Uses LangGraph for agent orchestration with nodes and edges
- **Node Types**:
  - `ChatbotNode`: Handles LLM interactions with tool support
  - `ToolNode`: Executes tool calls and returns responses
  - `HumanNode`: Manages human input interrupts
- **LLM Integration**: `src/buddy/llm/llm.py` - Uses LiteLLM for multi-provider support
- **Tool System**: Abstract `Tool` class in `src/buddy/tools/tool.py` with automatic schema generation

### Key Architectural Patterns

- **LangGraph State Management**: Uses StateGraph with InMemorySaver checkpointer
- **Agent-to-Agent (A2A) Server**: Implements A2A protocol for agent communication with skills and capabilities
- **Streaming Support**: Built-in streaming capabilities for real-time responses
- **Tool Schema Auto-generation**: Tools automatically generate OpenAI-compatible schemas from type hints
- **Conditional Routing**: Uses `tools_condition` and `end_condition` for flow control

### Directory Structure

- `src/buddy/` - Main package
  - `agents/` - Specialized agents (e.g., researcher with web search)
  - `cli/` - CLI presentation layer
  - `llm/` - LLM integration and utilities
  - `tools/` - Tool implementations
  - `exp/` - Experimental features
- `tests/` - Test suite
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
