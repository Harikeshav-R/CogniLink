from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.config import Config
from app.core.db import get_session, init_db


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
