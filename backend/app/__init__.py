import asyncio
import io
from contextlib import asynccontextmanager

from PIL import Image
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Config
from app.core.db import get_session, init_db
from app.shared.frame_broadcaster import frame_broadcaster
from app.workflows.object_permanence.worker import object_permanence_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    An asynchronous context manager to handle application startup and shutdown events.
    It initializes the database, starts a resilient background worker for object
    permanence analysis, and ensures graceful shutdown of the worker task.
    """
    # On Startup
    logger.info("Application lifespan starting...")
    logger.debug("Executing startup events.")

    # Setup the database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialization complete.")

    # Define a resilient manager for the object permanence worker
    async def worker_manager():
        """
        A resilient manager that runs the object permanence worker in a loop.
        If the worker crashes, it logs the error and restarts it after a delay.
        """
        while True:
            try:
                logger.info("Starting object permanence worker...")
                # get_session() is an async generator that handles session creation and cleanup
                async for db_session in get_session():
                    await object_permanence_worker(db_session)
            except Exception as e:
                # If the worker crashes, log the error and restart after a delay
                logger.error(f"Object permanence worker crashed with error: {e}. Restarting in 5 seconds...", exc_info=True)
                await asyncio.sleep(5)

    # Create the background task
    logger.info("Creating background task for object permanence worker manager...")
    task = asyncio.create_task(worker_manager())
    logger.info("Object permanence worker task created and running in the background.")

    yield

    # On Shutdown
    logger.info("Application lifespan shutting down...")
    logger.debug("Executing shutdown events.")
    logger.info("Cancelling object permanence worker task...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Object permanence worker task cancelled successfully.")
    logger.info("Application shutdown complete.")


app = FastAPI(lifespan=lifespan, title="CogniLink Backend", version="1.0.0")

if Config.DEBUG:
    logger.info("DEBUG mode is on. Adding CORS middleware for development.")
    # CORS Middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def root():
    """A simple endpoint to confirm the API is running."""
    logger.debug("Root endpoint '/' accessed.")
    return {"message": "CogniLink API is running."}


@app.get("/api/db-version")
async def get_db_version(session: AsyncSession = Depends(get_session)):
    """
    Tests the database connection by retrieving the PostgreSQL version.
    """
    logger.info("Request received for '/api/db-version' endpoint.")
    try:
        logger.debug("Executing query to get database version.")
        result = await session.exec(select(func.version()))
        version = result.scalar_one_or_none()
        logger.info(f"Successfully retrieved database version: {version}")
        return {"db_version": version}

    except Exception as e:
        logger.error(f"Database connection failed at '/api/db-version': {e}", exc_info=True)
        return {"error": f"Database connection failed: {e}"}


@app.websocket("/ws/object-permanence")
async def websocket_endpoint(websocket: WebSocket):
    """
    Handles the WebSocket connection for the object permanence workflow.
    It accepts a connection, receives image frames as bytes, converts them
    to PIL Images, and broadcasts them for processing.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from client: {websocket.client.host}:{websocket.client.port}")
    try:
        while True:
            logger.trace("WebSocket waiting to receive bytes...")
            data = await websocket.receive_bytes()
            logger.debug(f"Received {len(data)} bytes from WebSocket.")
            try:
                # Convert the received bytes into a PIL Image
                logger.trace("Decoding bytes into a PIL Image...")
                frame = Image.open(io.BytesIO(data))
                logger.debug(f"Frame decoded successfully: size={frame.size}, mode={frame.mode}")
                # Update the frame in the broadcaster for the worker to pick up
                logger.trace("Broadcasting frame to subscribers...")
                frame_broadcaster.broadcast(frame)
                logger.trace("Frame broadcasted.")
            except Exception as e:
                logger.error(f"Error processing frame from WebSocket: {e}", exc_info=True)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected by client: {websocket.client.host}:{websocket.client.port}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket endpoint: {e}", exc_info=True)
