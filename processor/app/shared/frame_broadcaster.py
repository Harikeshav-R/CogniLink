import asyncio
from typing import Any

from loguru import logger


class FrameBroadcaster:
    def __init__(self):
        self._subscribers: set[asyncio.Queue] = set()

    async def broadcast(self, data: Any) -> None:
        """
        Broadcast data to all active subscribers.

        This method iterates over all active subscriber queues and sends the provided
        data to each of them. If a queue is full, the data is dropped, and a warning
        is logged. The method ensures that the broadcasting process is non-blocking
        to maintain continuity of the stream.

        :param data: The data to be broadcasted to all subscriber queues.
        :type data: Any

        :return: None
        :rtype: None
        """
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
        """
        Subscribe to a message queue with a specified maximum size.

        This method allows subscribing to a message queue, creating a new
        asynchronous queue with the specified maximum size. The created queue
        is added to the list of subscribers.

        :param queue_size: The maximum size of the queue. Defaults to 1000.
        :type queue_size: int, optional

        :return: An asyncio.Queue instance representing the subscribed queue.
        :rtype: asyncio.Queue
        """
        q = asyncio.Queue(maxsize=queue_size)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        """
        Removes a subscriber queue from the list of subscribers.

        This method is used to unsubscribe a previously registered queue
        from receiving updates or notifications. If the given queue is
        found in the list of subscribers, it will be removed.

        :param q: The queue to be removed from the list of subscribers.
        :type q: asyncio.Queue

        :return: None
        :rtype: None
        """
        if q in self._subscribers:
            self._subscribers.remove(q)

    @staticmethod
    async def get_strict_batch(queue: asyncio.Queue, n: int) -> list[Any]:
        """
        Asynchronously retrieves a strict batch of items from the given async queue.

        The method collects exactly `n` items from the provided asyncio.Queue instance
        and returns them as a list. The `task_done` method is called for each item
        immediately after retrieval. This method ensures that the returned batch
        contains the exact number of requested items.

        :param queue: The asyncio.Queue instance from which items are retrieved.
        :type queue: asyncio.Queue

        :param n: The number of items to retrieve from the queue.
        :type n: int

        :return: A list containing exactly `n` items retrieved from the queue.
        :rtype: list[Any]
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
        Retrieve a batch of items from an asyncio.Queue in a greedy manner.

        This static method retrieves up to `n` items from the given asyncio.Queue. It first
        waits for at least one item to ensure that the returned list is never empty, then
        attempts to retrieve additional items already present in the queue without blocking.
        The method ensures that the items retrieved are marked as processed using `task_done`.

        :param queue: The asyncio.Queue instance from which items are retrieved.
        :type queue: asyncio.Queue

        :param n: The number of items to retrieve from the queue.
        :type n: int

        :return: A list containing upto `n` items retrieved from the queue.
        :rtype: list[Any]
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
        """
        Fetches a batch of items from an asyncio.Queue within a specified timeout period.

        This static method retrieves items from the provided asyncio.Queue up to a maximum
        number `n` within the time limit given by `timeout` (in seconds). If the timeout
        is reached before `n` items have been collected, the method returns the items
        gathered so far in a list.

        :param queue: The asyncio.Queue instance from which items are retrieved.
        :type queue: asyncio.Queue

        :param n: The number of items to retrieve from the queue.
        :type n: int

        :param timeout: The maximum time to wait for items in seconds.
        :type timeout: float

        :return: A list containing upto `n` items retrieved from the queue until the timeout.
        :rtype: list[Any]
        """
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
