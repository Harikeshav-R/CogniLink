from loguru import logger


class Constants:
    """
    Defines constant values for the application.
    This class provides default configurations and settings that are used
    across the application, ensuring consistency and ease of maintenance.
    """
    DEBUG = "true"

    DEFAULT_POSTGRES_HOST: str = "localhost"
    DEFAULT_POSTGRES_PORT: str = "5432"
    DEFAULT_POSTGRES_USER: str = "user"
    DEFAULT_POSTGRES_PASSWORD: str = "password"
    DEFAULT_POSTGRES_DB: str = "db"


logger.info("Application constants defined.")
