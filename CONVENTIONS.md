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
