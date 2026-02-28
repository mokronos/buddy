from pydantic_ai import RunContext

from buddy.agent.deps import AgentDeps


def _format_environment_error(action: str, error: Exception) -> str:
    message = str(error).strip() or error.__class__.__name__
    if "absolute paths must stay inside /workspace" in message or "path traversal is not allowed" in message:
        return (
            f"Could not {action}: {message}. "
            "Try again with paths inside /workspace only, for example './file.txt' or '/workspace/file.txt'."
        )
    return f"Could not {action}: {message}. Try again with a simpler command or check the file path under /workspace."


def environment_exec(ctx: RunContext[AgentDeps], command: str, timeout_s: int = 30) -> str:
    """Run a shell command inside the agent's environment container."""
    try:
        result = ctx.deps.environment_manager.exec(ctx.deps.session_id, command, timeout_s=timeout_s)
    except Exception as error:
        return _format_environment_error("run command", error)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if result.exit_code == 0:
        return stdout

    details = stderr if stderr else stdout
    return (
        f"Command failed with exit code {result.exit_code}. Output: {details}. "
        "Try commands that operate in /workspace (for example: 'pwd', 'ls', or 'ls /workspace')."
    )


def environment_read_file(ctx: RunContext[AgentDeps], path: str) -> str:
    """Read a UTF-8 text file from /workspace inside the environment container."""
    try:
        return ctx.deps.environment_manager.read_file(ctx.deps.session_id, path)
    except Exception as error:
        return _format_environment_error("read file", error)


def environment_write_file(ctx: RunContext[AgentDeps], path: str, content: str) -> str:
    """Write a UTF-8 text file to /workspace inside the environment container."""
    try:
        ctx.deps.environment_manager.write_file(ctx.deps.session_id, path, content)
    except Exception as error:
        return _format_environment_error("write file", error)
    else:
        return f"Wrote file: {path}"


def environment_patch_file(
    ctx: RunContext[AgentDeps],
    path: str,
    old_text: str,
    new_text: str,
    count: int = 1,
) -> str:
    """Replace text in a file inside the environment container."""
    try:
        replaced = ctx.deps.environment_manager.patch_file(
            owner_id=ctx.deps.session_id,
            path=path,
            old_text=old_text,
            new_text=new_text,
            count=count,
        )
    except Exception as error:
        return _format_environment_error("patch file", error)
    else:
        return f"Patched file: {path} (replacements={replaced})"
