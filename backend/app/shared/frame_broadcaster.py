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
        Stops the broadcaster and notifies all waiting consumers to exit.
        """
        async def _notify():
            async with self._condition:
                self.is_running = False
                self._condition.notify_all()
                logger.info("Stop signal broadcasted to all consumers.")

        logger.info("Stopping FrameBroadcaster...")
        try:
            # Schedule the notification on the running event loop
            asyncio.create_task(_notify())
        except RuntimeError as e:
            logger.error(f"Could not schedule stop notification: {e}. "
                         f"This may happen if the event loop is not running.")
