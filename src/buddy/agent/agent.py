"""Simple agent implementation with tool calling and step streaming."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Generator
from inspect import signature
from typing import Any

from dotenv import load_dotenv

from buddy.llm.llm import call_llm

load_dotenv()

os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")


class Agent:
    """A small loop-based agent that can call an LLM and execute tools.

    The agent loops until the LLM returns a final answer without tool calls.
    It supports a step-wise streaming interface for observability.
    """

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    def _append_system_and_user(self, prompt: str) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        if self.description:
            messages.append({"role": "system", "content": self.description})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _coerce_message_to_dict(self, message: Any) -> dict[str, Any]:
        if isinstance(message, dict):
            return message
        if hasattr(message, "model_dump"):
            return message.model_dump()  # type: ignore[attr-defined]
        if hasattr(message, "__dict__"):
            return dict(message.__dict__)
        raise TypeError("Unsupported message type from LLM")

    def _extract_assistant_message(self, resp: Any) -> dict[str, Any]:
        choice = None
        if isinstance(resp, dict):
            choices = resp.get("choices", [])
            choice = choices[0] if choices else None
        elif hasattr(resp, "choices"):
            choice = resp.choices[0]
        if choice is None:
            raise ValueError("LLM returned no choices")
        msg = choice.get("message") if isinstance(choice, dict) else getattr(choice, "message", None)
        if msg is None:
            raise ValueError("LLM choice has no message")
        return self._coerce_message_to_dict(msg)

    def _maybe_print(self, should_print: bool, text: str) -> None:
        if should_print:
            print(text)

    def _call_tool(
        self,
        tool_name: str,
        raw_arguments: Any,
        run_config: dict[str, Any] | None,
        tool_registry: dict[str, Callable[..., Any]],
    ) -> tuple[str, str]:
        func = tool_registry.get(tool_name)
        if func is None:
            return (
                tool_name,
                json.dumps({"error": f"tool '{tool_name}' not found"}),
            )

        parsed_args: Any
        if isinstance(raw_arguments, str):
            try:
                parsed_args = json.loads(raw_arguments) if raw_arguments else {}
            except json.JSONDecodeError:
                parsed_args = {"_raw": raw_arguments}
        else:
            parsed_args = raw_arguments or {}

        try:
            func_sig = signature(func)
            if len(func_sig.parameters) >= 2:
                result = func(parsed_args, run_config)
            else:
                result = func(parsed_args)
        except Exception as exc:
            return (tool_name, json.dumps({"error": str(exc)}))

        if isinstance(result, (str, int, float, bool)):
            return (tool_name, str(result))
        try:
            return (tool_name, json.dumps(result))
        except TypeError:
            return (tool_name, json.dumps({"result": str(result)}))

    def stream(
        self,
        prompt: str,
        run_config: dict[str, Any] | None = None,
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_registry: dict[str, Callable[..., Any]] | None = None,
        max_steps: int = 25,
    ) -> Generator[dict[str, Any], None, dict[str, Any]]:
        """Run the agent loop and yield step-by-step events.

        Parameters:
            prompt: The initial user input.
            run_config: Configuration passed to both the LLM and tools. Supported keys include:
                - model, temperature, tool_choice, response_format, stream_print (bool)
            tools: OpenAI-style tool specs to pass to the LLM.
            tool_registry: Mapping from tool name to a Python callable. Callables can accept
                either (arguments) or (arguments, run_config).
            max_steps: Maximum assistant-tool cycles to prevent infinite loops.

        Yields:
            Event dicts for each assistant and tool step. Final return value contains
            the final assistant content and the full conversation history.
        """
        cfg = run_config or {}
        should_print: bool = bool(cfg.get("stream_print", True))
        model: str | None = cfg.get("model")
        temperature: float | None = cfg.get("temperature")
        tool_choice: Any | None = cfg.get("tool_choice")
        response_format: dict[str, Any] | None = cfg.get("response_format")

        tool_specs: list[dict[str, Any]] = tools or []
        registry: dict[str, Callable[..., Any]] = tool_registry or {}

        messages = self._append_system_and_user(prompt)

        steps_taken = 0
        final_content: str | None = None

        while steps_taken < max_steps:
            resp = call_llm(
                messages=messages,
                model=model or "github/gpt-4.1-mini",
                tools=tool_specs if tool_specs else None,
                tool_choice=tool_choice,
                response_format=response_format,
                temperature=temperature if temperature is not None else 0.7,
                stream=False,
            )

            assistant_message = self._extract_assistant_message(resp)
            assistant_content = assistant_message.get("content") or ""
            assistant_tool_calls = assistant_message.get("tool_calls") or []

            messages.append({
                "role": "assistant",
                "content": assistant_content,
                **({"tool_calls": assistant_tool_calls} if assistant_tool_calls else {}),
            })

            self._maybe_print(
                should_print, f"assistant: {assistant_content}" if assistant_content else "assistant: [tool calls]"
            )
            yield {"type": "assistant", "content": assistant_content, "raw": assistant_message}

            if assistant_tool_calls:
                for tool_call in assistant_tool_calls:
                    function_info = tool_call.get("function", {})
                    tool_name = function_info.get("name")
                    raw_args = function_info.get("arguments")
                    tool_call_id = tool_call.get("id", "")
                    if not tool_name:
                        continue

                    name_used, tool_output = self._call_tool(
                        tool_name=tool_name,
                        raw_arguments=raw_args,
                        run_config=cfg,
                        tool_registry=registry,
                    )

                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": name_used,
                        "content": tool_output,
                    }
                    messages.append(tool_message)
                    self._maybe_print(should_print, f"tool[{name_used}]: {tool_output}")
                    yield {"type": "tool", "name": name_used, "content": tool_output}

                steps_taken += 1
                continue

            final_content = assistant_content
            break

        result = {
            "final": final_content or "",
            "messages": messages,
        }
        return result

    def run(
        self,
        prompt: str,
        run_config: dict[str, Any] | None = None,
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_registry: dict[str, Callable[..., Any]] | None = None,
        max_steps: int = 25,
    ) -> dict[str, Any]:
        """Synchronous convenience wrapper around stream()."""
        last_result: dict[str, Any] = {}
        for _ in self.stream(
            prompt=prompt,
            run_config=run_config,
            tools=tools,
            tool_registry=tool_registry,
            max_steps=max_steps,
        ):
            pass
        # The generator's return value is accessible via StopIteration.value,
        # but since we consumed it in a for-loop, we re-run once to get it.
        gen = self.stream(
            prompt=prompt,
            run_config=run_config,
            tools=tools,
            tool_registry=tool_registry,
            max_steps=max_steps,
        )
        try:
            while True:
                next(gen)
        except StopIteration as stop:
            last_result = stop.value or {}
        return last_result
