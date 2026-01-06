import asyncio
from typing import Any, Tuple, Optional
from loguru import logger


class FrameBroadcaster:
    """
    A class that manages the broadcasting of video frames to multiple consumers.
    """

    def __init__(self):
        logger.trace("Initializing FrameBroadcaster...")
        self._current_frame: Optional[Any] = None
        self._version: int = 0
        self._condition = asyncio.Condition()
        self.is_running: bool = True
        logger.debug("FrameBroadcaster initialized with is_running=True.")

    async def publish_frame(self, frame: Any) -> None:
        """
        Updates the current frame and notifies all waiting consumers.

        :param frame: The new video frame to be broadcasted.
        :type frame: Any
        :return: None
        :rtype: None
        """
        logger.trace("Acquiring lock to publish a new frame...")
        async with self._condition:
            logger.trace("Lock acquired. Updating frame and version.")
            self._current_frame = frame
            self._version += 1
            logger.debug(f"Frame published. New version is {self._version}.")
            logger.trace("Notifying all waiting consumers...")
            self._condition.notify_all()
            logger.trace("Notification sent.")

    async def get_latest_frame(self, last_version: int) -> Tuple[Any, int]:
        """
        Waits for a new frame version and returns the latest frame and its version.

        :param last_version: The version of the last frame processed by the consumer.
        :type last_version: int
        :return: A tuple containing the latest frame and its version.
        :rtype: Tuple[Any, int]
        """
        logger.trace(f"Acquiring lock to get latest frame for consumer with last_version={last_version}.")
        async with self._condition:
            logger.trace(f"Lock acquired. Current version is {self._version}.")
            while self.is_running and self._version <= last_version:
                logger.trace(f"Consumer (last_version={last_version}) is waiting for new frame. Current version: {self._version}")
                await self._condition.wait()
                logger.trace(f"Consumer (last_version={last_version}) awakened. Checking condition... is_running={self.is_running}, current_version={self._version}")

            if not self.is_running:
                logger.warning(f"get_latest_frame returning due to shutdown. Broadcaster is no longer running. Current version: {self._version}")
                return self._current_frame, self._version

            logger.debug(f"New frame available for consumer (last_version={last_version}). Returning version {self._version}")
            return self._current_frame, self._version

    def stop(self) -> None:
        """
        Stops the broadcaster and notifies all waiting consumers to exit.
        """
        async def _notify():
            logger.trace("Acquiring lock to send stop notification...")
            async with self._condition:
                logger.trace("Lock acquired. Setting is_running to False.")
                self.is_running = False
                logger.trace("Notifying all consumers of shutdown.")
                self._condition.notify_all()
                logger.info("Stop signal has been broadcast to all consumers.")

        logger.info("Stopping FrameBroadcaster...")
        try:
            logger.trace("Creating task to handle stop notification.")
            asyncio.create_task(_notify())
        except RuntimeError as e:
            logger.error(f"Could not schedule stop notification: {e}. "
                         f"This may happen if the event loop is not running.", exc_info=True)
