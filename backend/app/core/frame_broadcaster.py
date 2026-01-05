import threading
import uuid
from collections import deque

from PIL.Image import Image
from loguru import logger


class FrameBroadcaster:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Creates or fetches the singleton instance of the FrameBroadcaster class, ensuring
        thread-safe initialization. If the instance already exists, it returns the same, 
        else it initializes the instance and creates a dictionary to store subscribers.

        :returns: The singleton instance of the FrameBroadcaster class
        :rtype: FrameBroadcaster
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(FrameBroadcaster, cls).__new__(cls)
                    # Dictionary to hold subscriber queues: { subscriber_id: deque }
                    cls._instance.subscribers = {}
                    logger.info("FrameBroadcaster singleton instance created")
        return cls._instance

    def subscribe(self, name: str = "agent") -> str:
        """
        Generates a unique subscription ID for a new subscriber, registers them with their
        own message buffer, and returns the ID. Each subscriber receives an independent 
        message buffer to prevent delays caused by slower subscribers. However, their 
        buffer will drop older messages if it exceeds the maximum length.

        :param name: Name of the subscriber. Defaults to "agent".
        :type name: str
        :return: A unique subscription ID for the newly registered subscriber.
        :rtype: str
        """
        sub_id = f"{name}_{uuid.uuid4().hex[:8]}"
        logger.debug(f"Generating subscription ID: {sub_id} for subscriber name: {name}")
        with self._lock:
            # Give every subscriber their own buffer.
            # If one agent is slow, it won't block the others,
            # but it will start dropping its own frames (maxlen=5).
            self.subscribers[sub_id] = deque(maxlen=5)
        logger.info(f"📡 New Subscriber Registered: {sub_id} (total subscribers: {len(self.subscribers)})")
        return sub_id

    def unsubscribe(self, sub_id: str):
        """
        Unsubscribes a subscriber identified by the given subscription ID.

        This method removes the subscriber associated with the provided subscription ID
        from the list of subscribers, if it exists. The operation is performed 
        within a thread-safe context to ensure consistency across multiple threads.

        :param sub_id: Subscription ID of the subscriber to be removed.
        :type sub_id: str
        :return: None.
        """
        with self._lock:
            if sub_id in self.subscribers:
                del self.subscribers[sub_id]
                logger.info(f"Subscriber unsubscribed: {sub_id} (remaining subscribers: {len(self.subscribers)})")
            else:
                logger.warning(f"Attempted to unsubscribe non-existent subscriber: {sub_id}")

    def broadcast(self, frame: Image):
        """
        Broadcasts a given frame to all subscribed queues.

        This method is designed to distribute a frame to all subscribers
        in a thread-safe manner. It ensures that the operation on the
        subscribers' queues is synchronized, preventing potential race
        conditions when multiple threads access shared resources.

        :param frame: The frame to be broadcasted to all subscribers.
        :type frame: Image
        """
        with self._lock:
            subscriber_count = len(self.subscribers)
            logger.debug(f"Broadcasting frame to {subscriber_count} subscriber(s)")
            for queue in self.subscribers.values():
                queue.append(frame)

    def get_frame(self, sub_id: str) -> Image | None:
        """
        Retrieve the next frame from a subscriber's queue.

        This method fetches and removes the next available image frame from the
        queue associated with the provided subscriber ID. It ensures thread-safe
        access to the deque by using the defined class setup. If the queue exists
        and contains frames, the next frame is returned. If not, the method
        returns `None`.

        :param sub_id: The unique identifier of the subscriber for which the frame
            is being requested.
        :type sub_id: str

        :return: The next available image frame for the subscriber, or `None` if the
            queue is empty or does not exist.
        :rtype: Image or None
        """
        # We don't need the heavy lock for reading from deque (it's atomic in Python),
        # but for strict safety in this specific class setup:
        queue = self.subscribers.get(sub_id)
        if queue and len(queue) > 0:
            frame = queue.popleft()
            logger.debug(f"Frame retrieved for subscriber {sub_id} (queue length: {len(queue)})")
            return frame
        logger.debug(f"No frame available for subscriber {sub_id} (queue empty or doesn't exist)")
        return None


# Global Instance
frame_broadcaster = FrameBroadcaster()
