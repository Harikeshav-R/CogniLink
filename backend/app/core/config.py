import os

from app.core.constants import Constants


class Config:
    DEBUG: bool = os.getenv("DEBUG", Constants.DEBUG) == "true"

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", Constants.DEFAULT_POSTGRES_HOST)
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", Constants.DEFAULT_POSTGRES_PORT)
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", Constants.DEFAULT_POSTGRES_USER)
    POSTGRES_PASSWORD: str = os.getenv(
        "POSTGRES_PASSWORD", Constants.DEFAULT_POSTGRES_PASSWORD
    )
    POSTGRES_DB: str = os.getenv("POSTGRES_LEADS_DB", Constants.DEFAULT_POSTGRES_DB)

    POSTGRES_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
