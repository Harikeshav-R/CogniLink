import asyncio
from loguru import logger
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
                logger.warning(f"A consumer queue is full! Dropping frame.")

    def subscribe(self, queue_size: int = 1000) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=queue_size)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)

    @staticmethod
    async def get_strict_batch(queue: asyncio.Queue, n: int) -> list[Any]:
        """
        Waits until exactly 'n' frames have arrived in the queue.
        Blocks indefinitely until the batch is full.
        """
        batch = []
        for _ in range(n):
            item = await queue.get()
            batch.append(item)
            # Mark as done immediately or handle it later depending on your logic
            queue.task_done()
        return batch

    @staticmethod
    async def get_greedy_batch(queue: asyncio.Queue, n: int) -> list[Any]:
        """
        Waits for at least 1 frame, then grabs any others currently
        sitting in the buffer up to 'n'. Returns immediately.
        """
        batch = []

        # 1. Wait for the first frame (blocking) so we don't return an empty list
        item = await queue.get()
        batch.append(item)
        queue.task_done()

        # 2. Grab subsequent frames if they are already there (non-blocking)
        # We loop n-1 times
        for _ in range(n - 1):
            if queue.empty():
                break
            try:
                item = queue.get_nowait()
                batch.append(item)
                queue.task_done()
            except asyncio.QueueEmpty:
                break

        return batch

    @staticmethod
    async def get_timed_batch(queue: asyncio.Queue, n: int, timeout: float) -> list[Any]:
        batch = []

        # Calculate when we should stop waiting
        end_time = asyncio.get_running_loop().time() + timeout

        while len(batch) < n:
            remaining = end_time - asyncio.get_running_loop().time()
            if remaining <= 0:
                break  # Timeout reached, return what we have

            try:
                # Wait for the next item with a timeout
                item = await asyncio.wait_for(queue.get(), timeout=remaining)
                batch.append(item)
                queue.task_done()
            except asyncio.TimeoutError:
                break  # Timeout reached during wait

        return batch
