"""Event system for state changes."""
from enum import Enum, auto
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types."""
    # Playback events
    PLAYBACK_STARTED = auto()
    PLAYBACK_PAUSED = auto()
    PLAYBACK_STOPPED = auto()
    PLAYBACK_ENDED = auto()
    TRACK_CHANGED = auto()
    POSITION_CHANGED = auto()
    VOLUME_CHANGED = auto()
    MUTE_TOGGLED = auto()
    
    # Playlist events
    PLAYLIST_CHANGED = auto()
    TRACK_ADDED = auto()
    TRACK_REMOVED = auto()
    PLAYLIST_CLEARED = auto()
    PLAYLIST_LOADED = auto()
    PLAYLIST_SAVED = auto()
    
    # Shuffle/Repeat events
    SHUFFLE_TOGGLED = auto()
    REPEAT_CHANGED = auto()
    
    # Config events
    CONFIG_CHANGED = auto()
    THEME_CHANGED = auto()
    VISUALIZER_CHANGED = auto()
    
    # Error events
    ERROR_OCCURRED = auto()
    RECOVERY_STARTED = auto()
    RECOVERY_COMPLETED = auto()


@dataclass
class Event:
    """Event data."""
    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type.name,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "source": self.source,
        }


class EventBus:
    """Async event bus for publishing and subscribing to events."""
    
    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = {}
        self._async_subscribers: dict[EventType, list[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._history: list[Event] = []
        self._max_history = 100
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe to an event type (sync callback)."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def subscribe_async(self, event_type: EventType, callback: Callable[[Event], Any]):
        """Subscribe to an event type (async callback)."""
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
        if event_type in self._async_subscribers and callback in self._async_subscribers[event_type]:
            self._async_subscribers[event_type].remove(callback)
    
    def publish(self, event: Event):
        """Publish an event (non-blocking)."""
        try:
            self._event_queue.put_nowait(event)
            # Add to history
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)
        except asyncio.QueueFull:
            logger.warning(f"Event queue full, dropping event: {event.type}")
    
    def emit(self, event_type: EventType, data: dict[str, Any] = None, source: str = None):
        """Convenience method to create and publish an event."""
        event = Event(
            type=event_type,
            data=data or {},
            source=source,
        )
        self.publish(event)
    
    async def start(self):
        """Start the event processing loop."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_events())
    
    async def stop(self):
        """Stop the event processing loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _process_events(self):
        """Process events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=0.1
                )
                await self._dispatch_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _dispatch_event(self, event: Event):
        """Dispatch event to subscribers."""
        # Sync callbacks
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")
        
        # Async callbacks
        if event.type in self._async_subscribers:
            for callback in self._async_subscribers[event.type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in async event callback: {e}")
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 10) -> list[Event]:
        """Get event history."""
        events = self._history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        self._history.clear()


# Global event bus instance
event_bus = EventBus()
