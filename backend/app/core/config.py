import os
from loguru import logger
from app.core.constants import Constants


class Config:
    """
    Configuration class for the application.
    Loads environment variables and sets default values for all configurations.
    """
    DEBUG: bool = os.getenv("DEBUG", Constants.DEBUG) == "true"

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", Constants.DEFAULT_POSTGRES_HOST)
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", Constants.DEFAULT_POSTGRES_PORT)
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", Constants.DEFAULT_POSTGRES_USER)
    POSTGRES_PASSWORD: str = os.getenv(
        "POSTGRES_PASSWORD", Constants.DEFAULT_POSTGRES_PASSWORD
    )
    POSTGRES_DB: str = os.getenv("POSTGRES_LEADS_DB", Constants.DEFAULT_POSTGRES_DB)

    POSTGRES_URL: str = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GEMINI_PROVIDER: str = os.getenv("GEMINI_PROVIDER")
    GEMINI_FAST_MODEL: str = os.getenv("GEMINI_FAST_MODEL")
    GEMINI_SMART_MODEL: str = os.getenv("GEMINI_SMART_MODEL")
    GEMINI_VISION_MODEL: str = os.getenv("GEMINI_VISION_MODEL")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL")

    POLLINATIONS_ENDPOINT: str = os.getenv("POLLINATIONS_ENDPOINT")
    POLLINATIONS_API_KEY: str = os.getenv("POLLINATIONS_API_KEY")
    POLLINATIONS_PROVIDER: str = os.getenv("POLLINATIONS_PROVIDER")
    POLLINATIONS_FAST_MODEL: str = os.getenv("POLLINATIONS_FAST_MODEL")
    POLLINATIONS_SMART_MODEL: str = os.getenv("POLLINATIONS_SMART_MODEL")
    POLLINATIONS_VISION_MODEL: str = os.getenv("POLLINATIONS_VISION_MODEL")


logger.info("Loading application configuration...")
logger.info(f"DEBUG mode: {Config.DEBUG}")
logger.info(f"Database host: {Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}")
logger.info(f"Database user: {Config.POSTGRES_USER}")
logger.info(f"Database name: {Config.POSTGRES_DB}")

if Config.POSTGRES_PASSWORD:
    logger.debug("POSTGRES_PASSWORD is set.")
else:
    logger.warning("POSTGRES_PASSWORD is not set.")

if Config.GEMINI_API_KEY:
    logger.debug("GEMINI_API_KEY is set.")
else:
    logger.warning("GEMINI_API_KEY is not set.")

logger.info(f"Gemini provider: {Config.GEMINI_PROVIDER}")
logger.debug(f"Gemini fast model: {Config.GEMINI_FAST_MODEL}")
logger.debug(f"Gemini smart model: {Config.GEMINI_SMART_MODEL}")
logger.debug(f"Gemini vision model: {Config.GEMINI_VISION_MODEL}")
logger.debug(f"Gemini embedding model: {Config.GEMINI_EMBEDDING_MODEL}")

logger.info(f"Pollinations endpoint: {Config.POLLINATIONS_ENDPOINT}")
if Config.POLLINATIONS_API_KEY:
    logger.debug("POLLINATIONS_API_KEY is set.")
else:
    logger.warning("POLLINATIONS_API_KEY is not set.")

logger.info(f"Pollinations provider: {Config.POLLINATIONS_PROVIDER}")
logger.debug(f"Pollinations fast model: {Config.POLLINATIONS_FAST_MODEL}")
logger.debug(f"Pollinations smart model: {Config.POLLINATIONS_SMART_MODEL}")
logger.debug(f"Pollinations vision model: {Config.POLLINATIONS_VISION_MODEL}")
logger.info("Configuration loading complete.")
