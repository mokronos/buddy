"""
Runner script for the A2A agent example.
"""

import asyncio

from src.buddy.a2a_agent.example_server import main

if __name__ == "__main__":
    asyncio.run(main())
