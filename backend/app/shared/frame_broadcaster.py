import asyncio
from typing import Any, Tuple, Optional
from loguru import logger


class FrameBroadcaster:
    """
    A class that manages the broadcasting of video frames to multiple consumers.
    """

    def __init__(self):
        self._current_frame: Optional[Any] = None
        self._version: int = 0
        self._condition = asyncio.Condition()
        self.is_running: bool = True
        logger.debug("FrameBroadcaster initialized.")

    async def publish_frame(self, frame: Any) -> None:
        """
        Updates the current frame and notifies all waiting consumers.

        :param frame: The new video frame to be broadcasted.
        :type frame: Any
        :return: None
        :rtype: None
        """
        async with self._condition:
            self._current_frame = frame
            self._version += 1
            logger.trace(f"Frame updated to version {self._version}.")
            self._condition.notify_all()

    async def get_latest_frame(self, last_version: int) -> Tuple[Any, int]:
        """
        Waits for a new frame version and returns the latest frame and its version.

        :param last_version: The version of the last frame processed by the consumer.
        :type last_version: int
        :return: A tuple containing the latest frame and its version.
        :rtype: Tuple[Any, int]
        """
        async with self._condition:
            while self.is_running and self._version <= last_version:
                logger.trace(f"Consumer waiting for version > {last_version}. Current: {self._version}")
                await self._condition.wait()

            if not self.is_running:
                logger.debug(f"get_latest_frame interrupted: Broadcaster is no longer running. Returning current state (v{self._version}).")
                return self._current_frame, self._version

            logger.debug(f"Consumer retrieving new frame version: {self._version}")
            return self._current_frame, self._version

    def stop(self) -> None:
        """
        Stops the broadcaster and notifies all waiting consumers.

        :return: None
        :rtype: None
        """
        logger.info("Stopping FrameBroadcaster and notifying all consumers.")
        self.is_running = False
        # We need to notify all waiting tasks so they can exit their wait loops
        # This requires an event loop, so if called from sync code, it might need handling.
        # Assuming this is called within the same thread/loop context or we use thread-safe notification.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self._notify_stop(), loop)
            else:
                logger.warning("Event loop not running; consumers might remain suspended.")
        except RuntimeError:
            logger.error("No event loop found while attempting to stop broadcaster.")

    async def _notify_stop(self) -> None:
        async with self._condition:
            self._condition.notify_all()
            logger.debug("Broadcasted stop signal to all consumers.")
