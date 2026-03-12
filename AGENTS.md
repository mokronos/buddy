# AGENTS.md

## Project Overview

Buddy is an autonomous LLM platform built around a server/client architecture.

- The **server** is the core system: it creates and manages agents, and exposes them over the A2A protocol.
- **Clients** connect to the server to communicate with and manage those agents.
- `app/` is one of those clients. Always check app/AGENTS.md when working on the frontend app.

The goal is to build a JARVIS-like assistant with strong tooling and extensible agent workflows.

## Architecture Notes

- Do not do any work in legacy TUIs unless explicitly requested.
- Prefer changes that strengthen the server/client + A2A direction.

## Development Stage Policy

- This project is currently in heavy development; do **not** add compatibility layers, backward-compatibility shims, dual codepaths, or legacy fallbacks unless explicitly requested.
- Prefer clean replacements and direct migrations, even when they are breaking changes.
- Remove obsolete paths as part of refactors instead of keeping temporary compatibility code around.
- Always rebuild images when changing related code

## Development Environment

- **Python Version**: Requires Python 3.13+
- **Package Manager**: Use `uv` for all project operations instead of pip
- **Frontend Package Manager**: Use `bun` for JavaScript/TypeScript work in `app/`
- **Virtual Environment**: Managed via `uv sync`, but still available at `.venv`
- **Typing Imports**: Do not use `from __future__ import annotations` (Python 3.13+ runtime)

## General Commands

- Use `uv run <file>` instead of `python <file>` to automatically use the virtual environment for the scripts
- Use `bun` instead of `npm` inside `app/` for install/build/dev tasks
