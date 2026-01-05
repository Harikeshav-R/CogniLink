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
    # On Startup
    logger.info("Starting application lifespan...")

    # Setup the database
    await init_db()

    # Define a resilient manager for the object permanence worker
    async def worker_manager():
        while True:
            try:
                logger.info("Starting object permanence worker...")
                # get_session() is an async generator that handles session creation and cleanup
                async for db_session in get_session():
                    await object_permanence_worker(db_session)
            except Exception as e:
                # If the worker crashes, log the error and restart after a delay
                logger.error(f"Object permanence worker crashed with error: {e}. Restarting in 5 seconds...")
                await asyncio.sleep(5)

    # Create the background task
    task = asyncio.create_task(worker_manager())
    logger.info("Object permanence worker task created.")

    yield

    # On Shutdown
    logger.info("Shutting down application lifespan...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Object permanence worker task cancelled successfully.")


app = FastAPI(lifespan=lifespan)

if Config.DEBUG:
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
    return {"message": "Hello World"}


@app.get("/api/db-version")
async def get_db_version(session: AsyncSession = Depends(get_session)):
    """
    Tests the database connection by retrieving the PostgreSQL version.
    """
    try:
        result = await session.exec(select(func.version()))
        version = result.first()
        return {"db_version": version}

    except Exception as e:
        return {"error": f"Database connection failed: {e}"}


@app.websocket("/ws/object-permanence")
async def websocket_endpoint(websocket: WebSocket):
    """
    Handles the WebSocket connection for the object permanence workflow.
    Receives frames from a client and passes them to the frame broadcaster.
    """
    await websocket.accept()
    logger.info("Object permanence websocket connected.")
    try:
        while True:
            data = await websocket.receive_bytes()
            try:
                # Convert the received bytes into a PIL Image
                frame = Image.open(io.BytesIO(data))
                # Update the frame in the broadcaster for the worker to pick up
                frame_broadcaster.broadcast(frame)
            except Exception as e:
                logger.error(f"Error processing frame from websocket: {e}")

    except WebSocketDisconnect:
        logger.info("Object permanence websocket disconnected.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the websocket: {e}")
