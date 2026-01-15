# buddy

Personal AI assistant.

# Repository Overview

This repository offers a personal ai assistant.

# Purpose

The primary goal is to build a JARVIS-like assistant that not only performs diverse tasks but also has the ability to:

- Adjust its own system prompt dynamically.
- Learn new behaviors and create reusable tools or behaviors for future use.

This design enables continuous learning and improvement, making the assistant more effective and personalized with use.

# Tools

- **Planner / Notetaking Application:** Helps organize tasks and thoughts efficiently.
- **Model Context Protocol (MCP) Installer/Manager:** Manages and installs MCP servers, and adds them to the model context
- **Code Interpreter / Typescript REPL:** Allows execution of code for accessing/managing local files or accessing api's.
- **Settings Manager:** Manages the settings of the System itself.
    - get/set key/value pairs
- **Web Search:** Allows searching the web for information.
    - web_search: just searching (with summaries)
    - web_fetch: fetching full pages

# Potential Code tool execution

- All tools should be available as ts packages
    - model can just write code with them
    - e.g. fetch page --> parse with code --> console.log result --> read it
- typescript instead of python
- load docs/definitions dynamically

# Important Components

- Context Manager: Manages the context of the LLM, including the message history (system message, user messages, tool messages), and tools.
- Reflexion: Model should reflect on its last x actions and feedback from user and adjust its prompt and skills accordingly. Could also include writing a new tool/skill.

# Getting Started

To run the server:

```
uv run buddy server
```

To connect with the CLI client:

```
uv run buddy chat
```
