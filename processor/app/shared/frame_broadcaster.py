import asyncio
from typing import Any


class FrameBroadcaster:
    def __init__(self):
        self._subscribers: set[asyncio.Queue] = set()

    async def broadcast(self, data: Any):
        # Send data to every active queue
        # We iterate over a copy so subscribers can leave safely
        for q in list(self._subscribers):
            try:
                # If a queue is full, we log it.
                # For critical data, use 'await q.put(data)' but this WILL block
                # the entire stream if one consumer is full.
                # Using 'put_nowait' ensures the camera stream never pauses.
                q.put_nowait(data)
            except asyncio.QueueFull:
                print(f"Warning: A consumer queue is full! Dropping frame.")

    def subscribe(self, queue_size: int = 1000) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=queue_size)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)


frame_broadcaster = FrameBroadcaster()
