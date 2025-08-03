# Examples

This directory contains example scripts demonstrating how to use the Buddy agent system with tool calling functionality.

## Available Examples

- `basic_agent.py` - Demonstrates the full agent loop with tool calling. Creates an agent with PersonalInfoTool and runs it with the prompt "How old is Basti? Use the personal_information tool." Shows the complete flow: prompt → LLM → tool call → response.

## Running Examples

```bash
# From the project root (requires API key, e.g., GOOGLE_API_KEY)
uv run src/buddy/examples/basic_agent.py
```

## What the Examples Demonstrate

The examples show:

1. **Tool Integration**: How to use existing tools (like `PersonalInfoTool`) with the agent
2. **Natural Language Queries**: Agent automatically decides when to use tools based on user queries
3. **Direct Tool Calls**: Explicit tool execution via `use_<tool_name>` skills
4. **Error Handling**: How the agent handles unknown data and invalid requests
5. **Real LLM Integration**: Working examples with Gemini 2.0 Flash API

## Example Structure

Each example demonstrates:
- Tool adapter creation to bridge Tool base class with agent interface
- Agent initialization with tools and LLM client
- Multiple interaction patterns (queries, direct calls, error cases)
- Proper response handling and display

## PersonalInfoTool

The examples use the existing `PersonalInfoTool` which:
- Looks up personal information by name
- Currently has information for "basti"
- Handles case-insensitive matching
- Returns appropriate messages for unknown names
