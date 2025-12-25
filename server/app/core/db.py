from typing import Generator

from sqlmodel import create_engine, Session, SQLModel

from app.core.config import Config

engine = create_engine(Config.POSTGRES_URL)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
