import time

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from loguru import logger

from app.core.config import Config
from app.crud.object_permanence import create_log_entry
from app.workflows.object_permanence.state import State


async def save_analysis(state: State) -> dict:
    """
    Processes the filtered results within a given state, computes embeddings for the
    content in batches, creates log entries in the database, and returns a status 
    dictionary upon completion.

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

    # Extract all content strings to embed them in a single batch call
    contents = [entry.content for entry in state.filtered_results.entries]
    logger.debug(f"Extracted {len(contents)} content strings for embedding")

    if not contents:
        logger.debug("No content to save, returning empty dict")
        return {}

    logger.debug(f"Batch embedding {len(contents)} entries")
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model=Config.GEMINI_EMBEDDING_MODEL,
        google_api_key=Config.GEMINI_API_KEY,
        vertexai=False
    )

    # embed_documents handles batching internally
    all_embeddings = await embeddings_model.aembed_documents(contents)

    # Iterate through entries and their corresponding pre-computed embeddings
    for entry, embedding in zip(state.filtered_results.entries, all_embeddings):
        logger.debug(f"Creating log entry for object: {entry.object_name}")
        await create_log_entry(
            state.db_session,
            entry.content,
            embedding,
            current_time,
            entry.object_name,
            entry.log_type
        )

    logger.debug("Save analysis complete")
    logger.trace("Exiting save_analysis function")
    return {"save_status": True}
