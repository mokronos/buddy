"""
CLI client that connects to the A2A server.

This is the main CLI frontend that acts as an A2A client,
connecting to the A2A server to interact with the agent.
"""

import asyncio
import signal
import sys
import time
from types import FrameType

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status
from rich.text import Text


class CLIClient:
    """CLI client for interacting with the Buddy agent via A2A protocol."""

    def __init__(self) -> None:
        """Initialize the CLI client."""
        self.running = False
        self.console = Console()
        self.interrupted = False
        self.first_interrupt_time: float | None = None
        self.interrupt_timer_task: asyncio.Task | None = None

        # Set up signal handler for graceful Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum: int, frame: FrameType | None) -> None:
        """Handle Ctrl+C signal gracefully with double-press pattern."""
        current_time = time.time()

        if self.first_interrupt_time is None:
            # First Ctrl+C - clear line and start timer
            self.first_interrupt_time = current_time
            # Clear the current input line by moving cursor to beginning and clearing
            self.console.print("\r\033[K", end="")  # \r moves to start, \033[K clears line
            self.console.print("[yellow]^C[/yellow]")
            self.console.print("[yellow]Press Ctrl+C again within 1 second to exit...[/yellow]")
            self.console.print("[bold cyan]>[/bold cyan] ", end="")
            # Start timer to reset after 1 second
            try:
                loop = asyncio.get_event_loop()
                if self.interrupt_timer_task:
                    self.interrupt_timer_task.cancel()
                self.interrupt_timer_task = loop.create_task(self._reset_interrupt_timer())
            except RuntimeError:
                pass  # No event loop running
        elif current_time - self.first_interrupt_time < 1.0:
            # Second Ctrl+C within 1 second - exit gracefully
            self.console.print("\r\033[K", end="")  # Clear current line
            self.console.print("[yellow]⚠️  Interrupted by user[/yellow]")
            self.console.print("[dim]Goodbye! 👋[/dim]")
            # Force immediate exit
            import os

            os._exit(0)
        else:
            # Reset if too much time passed, treat as first Ctrl+C
            self.first_interrupt_time = current_time
            self.console.print("\r\033[K", end="")  # Clear line
            self.console.print("[yellow]^C[/yellow]")
            self.console.print("[yellow]Press Ctrl+C again within 1 second to exit...[/yellow]")
            self.console.print("[bold cyan]>[/bold cyan] ", end="")
            # Start timer to reset after 1 second
            try:
                loop = asyncio.get_event_loop()
                if self.interrupt_timer_task:
                    self.interrupt_timer_task.cancel()
                self.interrupt_timer_task = loop.create_task(self._reset_interrupt_timer())
            except RuntimeError:
                pass  # No event loop running

    async def _reset_interrupt_timer(self) -> None:
        """Reset the interrupt timer after 1 second."""
        await asyncio.sleep(1.0)
        self.first_interrupt_time = None
        if self.interrupt_timer_task:
            self.interrupt_timer_task = None

    def _print_welcome(self) -> None:
        """Print welcome message with Rich formatting."""
        welcome_panel = Panel(
            "[bold blue]Buddy Agent CLI[/bold blue]\n"
            "An autonomous LLM agent with comprehensive system tools.\n\n"
            "Commands:\n"
            "• Type your message and press Enter\n"
            "• [dim]exit, quit, q[/dim] - Exit the CLI\n"
            "• [dim]Ctrl+C twice[/dim] - Force exit",
            title="🤖 Welcome",
            border_style="blue",
        )
        self.console.print(welcome_panel)
        self.console.print()

    def _print_user_input(self, user_input: str) -> None:
        """Print user input with Rich formatting."""
        user_text = Text()
        user_text.append("👤 You: ", style="bold cyan")
        user_text.append(user_input, style="white")
        self.console.print(user_text)

    def _print_agent_response(self, response: str) -> None:
        """Print agent response with Rich formatting."""
        self.console.print()

        # Create agent header
        agent_header = Text()
        agent_header.append("🤖 Buddy: ", style="bold green")
        self.console.print(agent_header)

        # Print response content (support markdown if it looks like markdown)
        if any(marker in response for marker in ["```", "**", "*", "#", "`"]):
            try:
                md = Markdown(response)
                self.console.print(md, style="dim white")
            except Exception:
                # Fallback to plain text if markdown parsing fails
                self.console.print(response, style="dim white")
        else:
            self.console.print(response, style="dim white")

        self.console.print()

    def _print_error(self, error: str) -> None:
        """Print error message with Rich formatting."""
        error_panel = Panel(f"[red]{error}[/red]", title="❌ Error", border_style="red")
        self.console.print(error_panel)

    async def _simulate_streaming_response(self, message: str) -> None:
        """Simulate a streaming response for demo purposes."""
        # This will be replaced with actual A2A streaming
        import random

        words = message.split()
        response = ""

        with Status("[bold green]Buddy is thinking...", console=self.console, spinner="dots"):
            await asyncio.sleep(random.uniform(0.5, 1.5))  # Simulate thinking time

        self.console.print()
        agent_header = Text()
        agent_header.append("🤖 Buddy: ", style="bold green")
        self.console.print(agent_header)

        # Simulate streaming by updating the same line
        with Live(console=self.console, refresh_per_second=20) as live:
            for word in words:
                response += word + " "
                # Show current response with cursor
                display_text = Text()
                display_text.append(response + "▊", style="dim white")
                live.update(display_text)
                await asyncio.sleep(random.uniform(0.05, 0.15))

        # Print final response without cursor and move to next line
        self.console.print(response.strip(), style="dim white")
        self.console.print()

    async def _get_user_input(self) -> str:
        """Get user input asynchronously, checking for interruption."""
        self.console.print("[bold cyan]>[/bold cyan] ", end="")

        # Create a task for reading input
        loop = asyncio.get_event_loop()
        input_task = loop.run_in_executor(None, sys.stdin.readline)

        # Wait for input to complete
        try:
            user_input: str = await input_task

            # Reset interrupt timer if user typed something
            if user_input.strip():
                self.first_interrupt_time = None
                if self.interrupt_timer_task:
                    self.interrupt_timer_task.cancel()
                    self.interrupt_timer_task = None

            return user_input.strip()
        except asyncio.CancelledError:
            return ""

    async def run(self) -> None:
        """Run the CLI client main loop."""
        self.running = True

        # Print welcome message
        self._print_welcome()

        while self.running:
            try:
                # Get user input asynchronously
                user_input = await self._get_user_input()

                if not user_input:  # Handle EOF or empty input
                    self.console.print("[dim]Goodbye! 👋[/dim]")
                    self.running = False
                    break

                if user_input.lower() in ["exit", "quit", "q"]:
                    self.console.print("[dim]Goodbye! 👋[/dim]")
                    self.running = False
                    break

                # Print user input
                self._print_user_input(user_input)

                # TODO: Send request to A2A server
                # TODO: Handle streaming responses
                # For now, simulate a response
                demo_response = f"I received your message: '{user_input}'. This is a demo response that will be replaced with actual A2A communication. The response can include **markdown formatting** and `code snippets` for rich display."

                await self._simulate_streaming_response(demo_response)

            except KeyboardInterrupt:
                # This shouldn't happen now due to signal handler, but keep as fallback
                continue
            except EOFError:
                self.console.print("\n[dim]Goodbye! 👋[/dim]")
                self.running = False
                break
            except Exception as e:
                self._print_error(str(e))

    async def stop(self) -> None:
        """Stop the CLI client."""
        self.running = False
