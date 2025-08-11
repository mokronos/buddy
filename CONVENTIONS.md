# Conventions

Follow these conventions at all times:

## Running

- Use `uv` for all project related tasks instead of pip
    - To run files, always use `uv run <file>` instead of `python <file>`
    - To install packages use `uv add <package>` instead of `pip install <package>`

## Testing

- For each implemented feature, add a test
- Run tests with `uv run pytest`

## General

- try to write code that is self-explanatory
- when creating a code file, always put it in the library folder (buddy) or a subfolder (exception for tests)

## Comments

- Only add comments to code that is not self-explanatory

## Typing

- Prefer built-in generics and PEP 604 unions:
  - Use `list`, `dict`, `set`, `tuple` instead of `typing.List`, `typing.Dict`, ...
  - Use `str | None` instead of `Optional[str]`
  - Use `collections.abc` for callables/iterables: `Callable`, `Generator`, `Iterable`, ...
  - Keep `from __future__ import annotations` in modules defining type hints
