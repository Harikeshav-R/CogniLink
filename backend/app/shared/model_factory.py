from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from loguru import logger

from app.core.config import Config


def init_google_genai_chat_model(model: str, api_key: str) -> BaseChatModel:
    """
    Initializes a Google Generative AI chat model using the specified model name and API key.

    This function configures the chat model with the provider and API key from the application's
    configuration.

    :param model: The name of the Google GenAI model to initialize.
    :type model: str
    :param api_key: The API key for accessing the Google GenAI service.
    :type api_key: str
    :return: An initialized chat model instance.
    :rtype: BaseChatModel
    """
    logger.info(f"Initializing Google GenAI chat model: {model}")
    logger.debug(f"Using provider: {Config.GEMINI_PROVIDER}")
    if not api_key:
        logger.error("Google GenAI API key is missing.")
        raise ValueError("API key for Google GenAI must be provided.")
    try:
        chat_model = init_chat_model(
            model=model,
            model_provider=Config.GEMINI_PROVIDER,
            api_key=api_key
        )
        logger.info(f"Successfully initialized Google GenAI model: {model}")
        return chat_model
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI model '{model}': {e}")
        raise


def init_pollinations_chat_model(model: str, api_key: str) -> BaseChatModel:
    """
    Initializes a Pollinations chat model with the specified model name, API key, and endpoint.

    This function configures the chat model using the provider, API key, and endpoint from
    the application's configuration.

    :param model: The name of the Pollinations model to initialize.
    :type model: str
    :param api_key: The API key for accessing the Pollinations service.
    :type api_key: str
    :return: An initialized chat model instance.
    :rtype: BaseChatModel
    """
    logger.info(f"Initializing Pollinations chat model: {model}")
    logger.debug(f"Using provider: {Config.POLLINATIONS_PROVIDER} and endpoint: {Config.POLLINATIONS_ENDPOINT}")
    if not api_key:
        logger.error("Pollinations API key is missing.")
        raise ValueError("API key for Pollinations must be provided.")
    try:
        chat_model = init_chat_model(
            model=model,
            model_provider=Config.POLLINATIONS_PROVIDER,
            api_key=api_key,
            base_url=Config.POLLINATIONS_ENDPOINT
        )
        logger.info(f"Successfully initialized Pollinations model: {model}")
        return chat_model
    except Exception as e:
        logger.error(f"Failed to initialize Pollinations model '{model}': {e}")
        raise
