import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.shared.frame_broadcaster import FrameBroadcaster

router = APIRouter(tags=["WebSockets"])


@router.websocket("/object-permanence")
async def object_permanence_ws(websocket: WebSocket):
    """
    WebSocket endpoint for the object permanence workflow.

    Accepts a WebSocket connection and receives video frames (as base64 encoded strings)
    at a rate of approximately 1 frame per second. Each received frame is published
    to the central FrameBroadcaster to be processed by the background workflow.

    The broadcaster instance is retrieved from the application's state, which is
    managed by the main application's lifespan event handler.
    """
    logger.trace("Incoming WebSocket connection request to /object-permanence.")
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "unknown"
    client_port = websocket.client.port if websocket.client else "unknown"
    logger.info(f"WebSocket connection accepted from {client_host}:{client_port}.")

    try:
        logger.debug("Attempting to retrieve FrameBroadcaster from application state...")
        broadcaster: FrameBroadcaster = websocket.app.state.frame_broadcaster
        logger.trace("FrameBroadcaster successfully retrieved.")
    except AttributeError:
        logger.error("Frame broadcaster not found in app state. Closing WebSocket connection.", exc_info=True)
        await websocket.close(code=1011, reason="Internal server error: Broadcaster not available.")
        return

    logger.debug(f"Starting to listen for frames from {client_host}:{client_port}.")
    try:
        while True:
            logger.trace("Waiting to receive text data from WebSocket...")
            frame = await websocket.receive_bytes()
            logger.debug(f"Received data chunk of size {len(frame)} bytes via WebSocket.")
            frame_b64 = base64.b64encode(frame).decode("utf-8")
            logger.trace("Publishing received frame to broadcaster...")
            await broadcaster.broadcast(frame_b64)
            logger.trace("Frame successfully published to broadcaster.")

    except WebSocketDisconnect as e:
        logger.warning(
            f"WebSocket disconnected from {client_host}:{client_port} with code {e.code}. Reason: {e.reason}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket handler for {client_host}:{client_port}: {e}",
                     exc_info=True)
        # It's good practice to close the connection gracefully if an unexpected error occurs.
        await websocket.close(code=1011, reason=f"An unexpected server-side error occurred.")
    finally:
        logger.info(f"Closed WebSocket connection for {client_host}:{client_port}.")
