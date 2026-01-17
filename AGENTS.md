# CLAUDE.md

## Project Overview

Buddy is an autonomous LLM agent with comprehensive system tools. It provides a command-line interface to interact with large language models enhanced with powerful tools including a planner/notetaking application, Model Context Protocol (MCP) installer/manager, and code interpreter/Python REPL. The goal is to build a JARVIS-like assistant with self-improvement capabilities.

## Development Environment

- **Python Version**: Requires Python 3.13+
- **Package Manager**: Use `uv` for all project operations instead of pip
- **Virtual Environment**: Managed via `uv sync`, but still available at `.venv`

## General Commands

- Use `uv run <file>` instead of `python <file>` to automatically use the virtual environment for the scripts
