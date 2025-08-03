"""
A2A event system and callbacks.

This module implements the event system for push notifications
and real-time updates to A2A clients.
"""

import asyncio
from collections.abc import Callable
from enum import Enum
from typing import Any


class EventType(Enum):
    """A2A event types."""

    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_PAUSED = "agent_paused"
    AGENT_RESUMED = "agent_resumed"
    TOOL_EXECUTED = "tool_executed"
    STATUS_UPDATE = "status_update"
    PROGRESS_UPDATE = "progress_update"


class A2AEventSystem:
    """Event system for A2A protocol notifications."""

    def __init__(self):
        """Initialize the event system."""
        self.listeners: dict[EventType, list[Callable]] = {}
        self.event_queue = asyncio.Queue()

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self.listeners:
            self.listeners[event_type].remove(callback)

    async def emit(self, event_type: EventType, data: Any = None):
        """Emit an event to all listeners."""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, data)
                    else:
                        callback(event_type, data)
                except Exception as e:
                    print(f"Error in event callback: {e}")

        # Also add to queue for external processing
        await self.event_queue.put({"type": event_type, "data": data})

    async def get_next_event(self):
        """Get the next event from the queue."""
        return await self.event_queue.get()
