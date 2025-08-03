"""
Buddy - Autonomous LLM Agent with System Tools

Main entry point for the Buddy CLI application.
"""

import asyncio

from buddy.cli.client import CLIClient


def main():
    """Main entry point for the Buddy CLI."""
    # TODO: Start A2A server in background
    # TODO: Connect CLI client to A2A server
    # For now, just run the CLI client directly
    cli = CLIClient()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
