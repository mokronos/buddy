# Repository Overview

This repository offers a command-line interface (CLI) to interact with a large language model (LLM) enhanced with a suite of powerful tools.
It aims to provide a versatile assistant capable of performing a wide range of tasks with adaptability and self-improvement capabilities.

# Tools

- **Planner / Notetaking Application:** Helps organize tasks and thoughts efficiently.
- **Model Context Protocol (MCP) Installer/Manager:** Manages and installs MCP servers, and adds them to the model context
- **Code Interpreter / Python REPL:** Allows execution and testing of code for the LLM

# Purpose

The primary goal is to build a JARVIS-like assistant that not only performs diverse tasks but also has the ability to:

- Adjust its own system prompt dynamically.
- Potentially fine-tune itself over time.
- Learn new behaviors and create reusable tools or behaviors for future use.

This design enables continuous learning and improvement, making the assistant more effective and personalized with use.

# Getting Started

To run the program just run

```
uv run buddy/main.py
```

To run tests

```
uv run pytest
```
