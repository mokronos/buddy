# Legacy TUI Note

Legacy TUIs are not an active development target in this repository.

Current client surfaces are:

- CLI commands in `src/buddy/cli.py`
  - `uv run buddy chat`
  - `uv run buddy ask "..."`
- Web app in `app/`

If terminal interaction is needed, use the CLI commands above against the control-plane A2A endpoint.
