from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.shared.frame_broadcaster import FrameBroadcaster

router = APIRouter(prefix="/ws", tags=["WebSockets"])


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
    await websocket.accept()
    logger.info("WebSocket connection accepted for object permanence.")

    try:
        broadcaster: FrameBroadcaster = websocket.app.state.frame_broadcaster
    except AttributeError:
        logger.error("Frame broadcaster not found in app state. Closing connection.")
        await websocket.close(code=1011, reason="Internal server error: Broadcaster not available.")
        return

    try:
        while True:
            frame_b64 = await websocket.receive_text()
            logger.debug(f"Received frame of size {len(frame_b64)} bytes via WebSocket.")
            await broadcaster.publish_frame(frame_b64)
            logger.trace("Frame published to broadcaster.")

    except WebSocketDisconnect:
        logger.warning("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"An error occurred in the WebSocket handler: {e}", exc_info=True)
        # It's good practice to close the connection gracefully if an unexpected error occurs.
        await websocket.close(code=1011, reason=f"An unexpected error occurred: {e}")
