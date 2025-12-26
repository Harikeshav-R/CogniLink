import time
from loguru import logger
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import Config
from app.crud.object_permanence import create_log_entry
from app.workflows.object_permanence.state import State


def get_embeddings(text: str) -> list[float]:
    """
    Gets the embeddings for a given text using the specified embedding model and API key.

    This function utilizes the Google Generative AI Embeddings model to generate a
    vector representation for the input text. It requires proper configuration of the
    Google API key to function correctly.

    :param text: The input text for which embeddings need to be generated.
    :type text: str
    :return: A list of floating-point values representing the embedding of the input text.
    :rtype: list[float]
    """
    logger.trace("Entering get_embeddings function")
    logger.debug(f"Getting embeddings for text: '{text}'")
    embeddings = GoogleGenerativeAIEmbeddings(model=Config.GEMINI_EMBEDDING_MODEL, google_api_key=Config.GEMINI_API_KEY)
    vector = embeddings.embed_query(text)
    logger.trace("Exiting get_embeddings function")
    return vector


def save_analysis(state: State) -> dict:
    """
    Processes the filtered results within a given state, computes embeddings for the
    content, creates log entries in the database, and returns a status dictionary upon
    completion.

    :param state: The current state containing filtered results and database session
                  information.
    :type state: State
    :return: A dictionary indicating the save completion status. Returns an empty
             dictionary if no filtered results are available for processing.
    :rtype: dict
    """
    logger.trace("Entering save_analysis function")
    if not state.filtered_results:
        logger.debug("No filtered results to save, returning empty dict")
        return {}

    current_time = time.time()
    logger.debug(f"Current time: {current_time}")

    for entry in state.filtered_results.entries:
        logger.debug(f"Processing entry: {entry.content}")
        embedding = get_embeddings(entry.content)
        logger.debug(f"Creating log entry for object: {entry.object_name}")
        create_log_entry(
            state.db_session,
            entry.content,
            embedding,
            current_time,
            entry.object_name
        )

    logger.debug("Save analysis complete")
    logger.trace("Exiting save_analysis function")
    return {"save_status": True}
