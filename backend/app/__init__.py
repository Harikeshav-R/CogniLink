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
from app.workflows.orchestrator.schemas import OrchestratorWorkflowState
from app.workflows.orchestrator.workflow import create_compiled_state_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On Startup
    logger.info("Application lifespan starting...")
    logger.trace("Initializing database...")
    await init_db()
    logger.info("Database initialization complete.")

    # Set up the frame broadcaster and runner
    logger.trace("Initializing FrameBroadcaster...")
    frame_broadcaster = FrameBroadcaster()
    app.state.frame_broadcaster = frame_broadcaster
    logger.info("Frame broadcaster initialized and attached to app state.")

    logger.trace("Creating background task for object permanence workflow...")
    runner_task = asyncio.create_task(object_permanence_workflow_runner(frame_broadcaster))
    logger.info("Object permanence workflow runner started as a background task.")

    logger.trace("Yielding control to the application...")
    yield
    logger.trace("Control returned from application. Starting shutdown sequence.")

    # On Shutdown
    logger.info("Application lifespan shutting down...")
    logger.trace("Cancelling object permanence workflow runner task...")
    runner_task.cancel()
    try:
        await runner_task
    except asyncio.CancelledError:
        logger.info("Object permanence workflow runner task successfully cancelled.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during workflow runner task cancellation: {e}", exc_info=True)
    logger.success("Application shutdown complete.")


app = FastAPI(lifespan=lifespan, title="CogniLink Processor Server", version="1.0.0")

logger.trace("Checking DEBUG mode for CORS middleware configuration.")
if Config.DEBUG:
    logger.info("DEBUG mode is enabled. Adding CORS middleware for development.")
    logger.trace(f"Allowed origins: {['http://localhost:5173', 'http://localhost:8000']}")
    # CORS Middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    logger.info("DEBUG mode is disabled. Skipping CORS middleware.")

# Include API routers
logger.trace("Including API routers...")
app.include_router(websockets_router, prefix="/api/ws", tags=["WebSockets"])
logger.debug("WebSockets router included with prefix '/api/ws'.")


@app.get("/")
async def root():
    """
    A simple endpoint to confirm the API is running.

    :return: A confirmation message.
    :rtype: dict
    """
    logger.debug("Request received for root endpoint '/'.")
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
        query = select(func.version())
        logger.debug(f"Executing query to get database version: {query}")
        result = await session.exec(query)
        version = result.scalar_one_or_none()

        if version:
            logger.info(f"Successfully retrieved database version: {version}")
            logger.trace(f"Returning database version in response.")
            return {"db_version": version}
        else:
            logger.warning("Database version query returned no result.")
            return {"error": "Could not retrieve database version."}

    except Exception as e:
        logger.error(f"Database connection failed at '/api/db-version': {e}", exc_info=True)
        return {"error": f"Database connection failed: {e}"}


@app.post("/api/query")
async def generate_response(query: str):
    """
    Generates a response based on the provided query using an orchestrator workflow.

    This function initializes a compiled state graph for the orchestrator workflow,
    sets up the initial state using the input query, and processes the workflow
    to obtain the final state. The final state is validated and the response
    is extracted for returning.

    :param query: The input query for which a response is to be generated.
    :type query: str
    :return: A dictionary containing the generated response based on the query.
    :rtype: dict
    """
    workflow = create_compiled_state_graph()
    initial_state = OrchestratorWorkflowState(query=query)
    final_state: OrchestratorWorkflowState = await workflow.ainvoke(initial_state)
    final_state = OrchestratorWorkflowState.model_validate(final_state)
    return {"response": final_state.response}
