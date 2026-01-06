import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.websockets import router as websockets_router
from app.core.config import Config
from app.core.db import get_session, init_db
from app.shared.frame_broadcaster import FrameBroadcaster
from app.workflows.object_permanence.runner import object_permanence_workflow_runner


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On Startup
    logger.info("Application lifespan starting...")
    await init_db()
    logger.info("Database initialization complete.")

    # Set up the frame broadcaster and runner
    frame_broadcaster = FrameBroadcaster()
    app.state.frame_broadcaster = frame_broadcaster
    logger.info("Frame broadcaster initialized.")

    runner_task = asyncio.create_task(object_permanence_workflow_runner(frame_broadcaster))
    logger.info("Object permanence workflow runner started.")

    yield

    # On Shutdown
    logger.info("Application lifespan shutting down...")
    frame_broadcaster.stop()
    logger.info("Frame broadcaster stopped.")
    runner_task.cancel()
    try:
        await runner_task
    except asyncio.CancelledError:
        logger.info("Object permanence workflow runner task successfully cancelled.")
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

# Include API routers
app.include_router(websockets_router, prefix="/api", tags=["WebSockets"])


@app.get("/")
async def root():
    """
    A simple endpoint to confirm the API is running.

    :return: A confirmation message.
    :rtype: dict
    """
    logger.debug("Root endpoint '/' accessed.")
    return {"message": "CogniLink API is running."}


@app.get("/api/db-version")
async def get_db_version(session: AsyncSession = Depends(get_session)):
    """
    Tests the database connection by retrieving the PostgreSQL version.

    :param session: The database session, injected by FastAPI's dependency system.
    :type session: AsyncSession
    :return: A dictionary containing the database version or an error message.
    :rtype: dict
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
