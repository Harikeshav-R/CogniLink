import io
from contextlib import asynccontextmanager
from typing import Optional

from PIL import Image
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.config import Config
from app.core.db import get_session, init_db
from app.workflows.object_permanence.state import State
from app.workflows.object_permanence.workflow import create_compiled_state_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On Startup

    # Setup the database
    init_db()

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
def root():
    return {"message": "Hello World"}


@app.get("/api/db-version")
def get_db_version(session: Session = Depends(get_session)):
    """
    Tests the database connection by retrieving the PostgreSQL version.
    """
    try:
        result = session.exec(select(func.version())).first()
        return {"db_version": result}

    except Exception as e:
        return {"error": f"Database connection failed: {e}"}


@app.post("/api/workflows/object-permanence")
async def run_object_permanence_workflow(
        session: Session = Depends(get_session),
        current_frame: UploadFile = File(...),
        previous_frame: Optional[UploadFile] = File(None),
):
    """
    Runs the object permanence workflow.

    This endpoint executes a LangGraph workflow to analyze images for object permanence.
    The workflow can perform two main types of analysis:
    1.  **Static Analysis**: Identifies objects in a single frame (`current_frame`).
    2.  **Differential Analysis**: Compares `current_frame` with `previous_frame` to detect changes.

    - If both `current_frame` and `previous_frame` are provided, the workflow will
      compare them. If they are different enough, it will run both static and
      differential analysis.
    - If only `current_frame` is provided, the workflow as currently implemented
      will not perform any analysis. For analysis to occur, both frames are required by the `check_frame_similarity` entrypoint.

    The state of the workflow after execution is returned, excluding non-serializable
    fields like images and the database session.
    """
    current_frame_img = Image.open(io.BytesIO(await current_frame.read()))
    current_frame_img.load()  # Force load the image data to prevent issues with lazy loading
    previous_frame_img = None
    if previous_frame:
        previous_frame_img = Image.open(io.BytesIO(await previous_frame.read()))
        previous_frame_img.load()  # Force load the image data

    initial_state = State(current_frame=current_frame_img, previous_frame=previous_frame_img, db_session=session)

    graph = create_compiled_state_graph()

    # The graph.invoke will return the final state.
    final_state = graph.invoke(initial_state)

    # The state contains non-serializable fields like images and db session.
    # We select the serializable fields to return.
    serializable_state = {
        key: value
        for key, value in final_state.items()
        if key not in ["current_frame", "previous_frame", "db_session"]
    }

    return serializable_state
