import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Config
from app.core.db import get_session, init_db
from app.workflows.object_permanence.state import State
from app.workflows.object_permanence.workflow import create_compiled_state_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On Startup

    # Setup the database
    await init_db()

    yield

    # On Shutdown
    pass


app = FastAPI(lifespan=lifespan)

if Config.DEBUG:
    # CORS Middleware for development
    # This allows the frontend (running on localhost:5173) to communicate with the backend.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Allows the dev frontend
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


@app.post("/api/workflows/object-permanence")
async def run_object_permanence_workflow(
        session: AsyncSession = Depends(get_session),
        video_clip: UploadFile = File(...),
):
    """
    Runs the object permanence workflow on a video clip.

    This endpoint receives a video clip, saves it to a temporary file, and
    triggers a LangGraph workflow. The workflow is responsible for extracting
    frames, analyzing them for object permanence, and storing the results.

    The state of the workflow after execution is returned, excluding non-serializable
    fields like the database session.
    """
    # Create a temporary file to store the video clip
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        content = await video_clip.read()
        tmp.write(content)
        video_path = tmp.name

    try:
        initial_state = State(video_path=video_path, db_session=session)

        graph = create_compiled_state_graph()

        # The graph.invoke will return the final state.
        final_state = await graph.ainvoke(initial_state)

        # The state contains non-serializable fields.
        # We select the serializable fields to return.
        serializable_state = {
            key: value
            for key, value in final_state.items()
            if key not in ["video_path", "frames", "db_session"]
        }

        return serializable_state
    finally:
        # Clean up the temporary file
        os.unlink(video_path)
