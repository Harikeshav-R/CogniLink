import threading
import uuid
from collections import deque

from PIL.Image import Image
from loguru import logger


class FrameBroadcaster:
    """
    A thread-safe singleton class for broadcasting image frames to multiple subscribers.
    Each subscriber receives frames on an independent queue, preventing slow consumers
    from blocking others.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Creates or returns the singleton instance of the FrameBroadcaster.
        This ensures that there is only one frame broadcaster throughout the application,
        providing a single point for frame distribution.
        """
        if cls._instance is None:
            logger.debug("FrameBroadcaster instance not found, creating a new one.")
            with cls._lock:
                logger.trace("Acquired lock for singleton creation.")
                if cls._instance is None:
                    cls._instance = super(FrameBroadcaster, cls).__new__(cls)
                    # Dictionary to hold subscriber queues: { subscriber_id: deque }
                    cls._instance.subscribers = {}
                    logger.info("FrameBroadcaster singleton instance created.")
                else:
                    logger.debug("Singleton instance already created by another thread.")
                logger.trace("Released lock for singleton creation.")
        else:
            logger.trace("Returning existing FrameBroadcaster instance.")
        return cls._instance

    def subscribe(self, name: str = "agent") -> str:
        """
        Registers a new subscriber and provides them with a unique subscription ID
        and a dedicated frame queue.

        :param name: An optional name for the subscriber for easier identification in logs.
        :return: A unique subscription ID string.
        """
        sub_id = f"{name}_{uuid.uuid4().hex[:8]}"
        logger.info(f"New subscription request from '{name}'. Generated ID: {sub_id}")
        with self._lock:
            logger.trace(f"Acquired lock to register subscriber {sub_id}.")
            # Each subscriber gets its own buffer. If one is slow, it won't block others,
            # but it will drop its own oldest frames if the deque fills up (maxlen=5).
            self.subscribers[sub_id] = deque(maxlen=5)
            logger.debug(f"Subscriber {sub_id} registered with a new deque (maxlen=5).")
            logger.trace(f"Released lock after registering subscriber {sub_id}.")
        logger.info(f"📡 Subscriber '{sub_id}' successfully registered. Total subscribers: {len(self.subscribers)}")
        return sub_id

    def unsubscribe(self, sub_id: str):
        """
        Removes a subscriber and their associated queue from the broadcaster.

        :param sub_id: The subscription ID of the subscriber to remove.
        """
        logger.info(f"Unsubscribe request for ID: {sub_id}")
        with self._lock:
            logger.trace(f"Acquired lock to unsubscribe subscriber {sub_id}.")
            if sub_id in self.subscribers:
                del self.subscribers[sub_id]
                logger.info(f"Subscriber '{sub_id}' successfully unsubscribed.")
            else:
                logger.warning(f"Attempted to unsubscribe non-existent subscriber ID: {sub_id}")
            logger.trace(f"Released lock after unsubscribing subscriber {sub_id}.")
        logger.debug(f"Total subscribers remaining: {len(self.subscribers)}")

    def broadcast(self, frame: Image):
        """
        Distributes a frame to all currently registered subscribers by adding
        it to each of their queues.

        :param frame: The PIL Image frame to be broadcast.
        """
        logger.debug(f"Request to broadcast a new frame of size {frame.size}.")
        with self._lock:
            logger.trace("Acquired lock to broadcast frame.")
            subscriber_count = len(self.subscribers)
            if subscriber_count > 0:
                logger.debug(f"Broadcasting frame to {subscriber_count} subscriber(s).")
                for sub_id, queue in self.subscribers.items():
                    queue.append(frame)
                    logger.trace(f"Appended frame to queue for subscriber '{sub_id}'.")
            else:
                logger.debug("No subscribers to broadcast to.")
            logger.trace("Released lock after broadcasting frame.")

    def get_frame(self, sub_id: str) -> Image | None:
        """
        Retrieves the next frame from a specific subscriber's queue.
        This is a non-blocking, thread-safe operation that returns a frame
        if one is available, otherwise returns None.

        :param sub_id: The unique ID of the subscriber.
        :return: A PIL Image frame, or None if the queue is empty.
        """
        logger.trace(f"Frame request from subscriber: {sub_id}")
        queue = self.subscribers.get(sub_id)
        if queue:
            try:
                # popleft() is an atomic operation in Python's deque
                frame = queue.popleft()
                logger.debug(f"Retrieved frame for subscriber {sub_id}. Remaining queue size: {len(queue)}")
                return frame
            except IndexError:
                logger.trace(f"No frame available for subscriber {sub_id} (queue is empty).")
                return None
        else:
            logger.warning(f"Subscriber '{sub_id}' not found when trying to get a frame.")
            return None


# Global Instance
logger.debug("Creating global instance of FrameBroadcaster.")
frame_broadcaster = FrameBroadcaster()
