# buddy

[![Release](https://img.shields.io/github/v/release/mokronos/buddy)](https://img.shields.io/github/v/release/mokronos/buddy)
[![Build status](https://img.shields.io/github/actions/workflow/status/mokronos/buddy/main.yml?branch=main)](https://github.com/mokronos/buddy/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/mokronos/buddy/branch/main/graph/badge.svg)](https://codecov.io/gh/mokronos/buddy)
[![Commit activity](https://img.shields.io/github/commit-activity/m/mokronos/buddy)](https://img.shields.io/github/commit-activity/m/mokronos/buddy)
[![License](https://img.shields.io/github/license/mokronos/buddy)](https://img.shields.io/github/license/mokronos/buddy)

An autonomous LLM agent with comprehensive system tools

- **Github repository**: <https://github.com/mokronos/buddy/>
- **Documentation** <https://mokronos.github.io/buddy/>

## Getting started with your project

### 1. Create a New Repository

First, create a repository on GitHub with the same name as this project, and then run the following commands:

```bash
git init -b main
git add .
git commit -m "init commit"
git remote add origin git@github.com:mokronos/buddy.git
git push -u origin main
```

### 2. Set Up Your Development Environment

Then, install the environment and the pre-commit hooks with

```bash
make install
```

This will also generate your `uv.lock` file

### 3. Run the pre-commit hooks

Initially, the CI/CD pipeline might be failing due to formatting issues. To resolve those run:

```bash
uv run pre-commit run -a
```

### 4. Commit the changes

Lastly, commit the changes made by the two steps above to your repository.

```bash
git add .
git commit -m 'Fix formatting issues'
git push origin main
```

You are now ready to start development on your project!
The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

To finalize the set-up for publishing to PyPI, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/codecov/).

## Releasing a new version



---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).

# ACTUAL

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
