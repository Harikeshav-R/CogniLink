from typing import Generator

from sqlmodel import create_engine, Session, SQLModel, text

from app.core.config import Config

engine = create_engine(Config.POSTGRES_URL)


def init_db() -> None:
    # 1. Enable the extension using a raw connection
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()

    # 2. Create tables
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
