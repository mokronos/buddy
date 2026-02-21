# AGENTS.md

## Project Overview

Buddy is an autonomous LLM platform built around a server/client architecture.

- The **server** is the core system: it creates and manages agents, and exposes them over the A2A protocol.
- **Clients** connect to the server to communicate with and manage those agents.
- `app/` is one of those clients.

The goal is to build a JARVIS-like assistant with strong tooling and extensible agent workflows.

## Architecture Notes

- Treat `tui/` and `tui_new/` as legacy codepaths.
- Do not do any work in legacy TUIs unless explicitly requested.
- Prefer changes that strengthen the server/client + A2A direction.

## Development Environment

- **Python Version**: Requires Python 3.13+
- **Package Manager**: Use `uv` for all project operations instead of pip
- **Virtual Environment**: Managed via `uv sync`, but still available at `.venv`
- **Typing Imports**: Do not use `from __future__ import annotations` (Python 3.13+ runtime)

## General Commands

- Use `uv run <file>` instead of `python <file>` to automatically use the virtual environment for the scripts

# Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Fail Fast on Errors

**Prefer explicit failures over synthetic fallback behavior.**

- If execution fails, raise an error instead of emitting fake/synthetic success-like artifacts.
- Use assertions for invariants that should never fail.
- Add fallback handling only when explicitly requested and clearly scoped.
- Preserve raw error context so failures are debuggable from logs/events.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
