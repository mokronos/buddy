# buddy

[![Release](https://img.shields.io/github/v/release/mokronos/buddy)](https://img.shields.io/github/v/release/mokronos/buddy)
[![Build status](https://img.shields.io/github/actions/workflow/status/mokronos/buddy/main.yml?branch=main)](https://github.com/mokronos/buddy/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/mokronos/buddy/branch/main/graph/badge.svg)](https://codecov.io/gh/mokronos/buddy)
[![Commit activity](https://img.shields.io/github/commit-activity/m/mokronos/buddy)](https://img.shields.io/github/commit-activity/m/mokronos/buddy)
[![License](https://img.shields.io/github/license/mokronos/buddy)](https://img.shields.io/github/license/mokronos/buddy)

An autonomous LLM agent with comprehensive system tools

- **Github repository**: <https://github.com/mokronos/buddy/>
- **Documentation** <https://mokronos.github.io/buddy/>

# Repository Overview

This repository offers a command-line interface (CLI) to interact with a large language model (LLM) enhanced with a suite of powerful tools.
It aims to provide a versatile assistant capable of performing a wide range of tasks with adaptability and self-improvement capabilities.

# Tools

- **Planner / Notetaking Application:** Helps organize tasks and thoughts efficiently.
- **Model Context Protocol (MCP) Installer/Manager:** Manages and installs MCP servers, and adds them to the model context
- **Code Interpreter / Python REPL:** Allows execution and testing of code for the LLM
- **Settings Manager:** Manages the settings of the System

# Code tool execution

- All tools should be available as packages
- ts > python
- load docs/definitions dynamically
- somehow attach user specific tokens in api calls

# Important Components

- Context Manager: Manages the context of the LLM, including the message history(, system message), and tools.

# Purpose

The primary goal is to build a JARVIS-like assistant that not only performs diverse tasks but also has the ability to:

- Adjust its own system prompt dynamically.
- Potentially fine-tune itself over time.
- Learn new behaviors and create reusable tools or behaviors for future use.

This design enables continuous learning and improvement, making the assistant more effective and personalized with use.

# Getting Started

To run the program just run

```
uv run src/buddy/main.py
```

# Development

Check out the Makefile for some useful commands.
