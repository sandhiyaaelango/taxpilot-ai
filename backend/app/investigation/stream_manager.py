import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, AsyncGenerator
from app.config.logging import get_logger

import time

logger = get_logger("stream_manager")

class InvestigationStreamManager:
    """
    In-memory pub/sub event stream manager for Server-Sent Events (SSE).
    Distributes live agent telemetry, ReAct loop steps, and MCP tool execution events
    to connected browser clients. Maintains an event buffer per investigation for initial sync.
    """
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def broadcast(self, investigation_id: str, event_type: str, payload: Dict[str, Any]):
        """Publish an event to all connected clients and store in history buffer."""
        event_data = {
            "event": event_type,
            "investigation_id": investigation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload
        }

        async with self._lock:
            # Buffer history (up to last 100 events per investigation)
            if investigation_id not in self._history:
                self._history[investigation_id] = []
            self._history[investigation_id].append(event_data)
            if len(self._history[investigation_id]) > 100:
                self._history[investigation_id].pop(0)

            # Send to active subscribers
            queues = self._subscribers.get(investigation_id, set())
            for q in list(queues):
                try:
                    q.put_nowait(event_data)
                except Exception as e:
                    logger.warning("failed_to_push_sse_event", error=str(e))

    async def subscribe(
        self,
        investigation_id: str,
        replay_only: bool = False,
        timeout: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to live investigation events with initial history replay.
        Supports replay_only for fast historical reads and bounded timeout for safe consumption.
        """
        queue: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            if investigation_id not in self._subscribers:
                self._subscribers[investigation_id] = set()
            self._subscribers[investigation_id].add(queue)

            # Send historical events first
            past_events = list(self._history.get(investigation_id, []))

        # Replay past events
        for past_event in past_events:
            yield f"data: {json.dumps(past_event)}\n\n"

        # If replay_only requested, terminate stream immediately after history
        if replay_only:
            async with self._lock:
                if investigation_id in self._subscribers:
                    self._subscribers[investigation_id].discard(queue)
                    if not self._subscribers[investigation_id]:
                        del self._subscribers[investigation_id]
            return

        # If history already contains a terminal event, terminate gracefully
        has_terminal_event = any(
            e.get("event") in ["investigation_completed", "investigation_failed", "investigation_paused_for_approval"]
            for e in past_events
        )
        if has_terminal_event:
            async with self._lock:
                if investigation_id in self._subscribers:
                    self._subscribers[investigation_id].discard(queue)
                    if not self._subscribers[investigation_id]:
                        del self._subscribers[investigation_id]
            return

        start_time = time.monotonic()
        try:
            while True:
                # Check timeout bounds if specified
                remaining = None
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed >= timeout:
                        break
                    remaining = timeout - elapsed

                poll_wait = min(remaining, 15.0) if remaining is not None else 15.0
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=poll_wait)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("event") in ["investigation_completed", "investigation_failed"]:
                        # Terminal event arrived, allow client a brief moment then stop
                        await asyncio.sleep(0.1)
                        break
                except asyncio.TimeoutError:
                    if timeout is not None and (time.monotonic() - start_time) >= timeout:
                        break
                    # Keep-alive heartbeat comment
                    yield ": keep-alive\n\n"
        finally:
            async with self._lock:
                if investigation_id in self._subscribers:
                    self._subscribers[investigation_id].discard(queue)
                    if not self._subscribers[investigation_id]:
                        del self._subscribers[investigation_id]

    def get_history(self, investigation_id: str) -> List[Dict[str, Any]]:
        return list(self._history.get(investigation_id, []))

stream_manager = InvestigationStreamManager()
