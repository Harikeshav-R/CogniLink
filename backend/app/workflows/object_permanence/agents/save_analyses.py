import time

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from loguru import logger

from app.core.config import Config
from app.crud.object_permanence import create_log_entry
from app.workflows.object_permanence.state import ObjectPermanenceState


async def save_analysis(state: ObjectPermanenceState) -> dict:
    logger.trace("Entering save_analysis function")

    current_time = time.time()
    contents = [entry.formatted_description for entry in state.formatted_analyses]
    logger.debug(f"Extracted {len(contents)} content strings for embedding")

    if not contents:
        logger.debug("No content to save, returning empty dict")
        return {}

    logger.debug("Initializing embedding model...")
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model=Config.GEMINI_EMBEDDING_MODEL,
        google_api_key=Config.GEMINI_API_KEY,
        vertexai=False
    )
    logger.debug("Embedding model initialized.")

    logger.debug(f"Batch embedding {len(contents)} entries...")
    # embed_documents handles batching internally
    all_embeddings = await embeddings_model.aembed_documents(contents)
    logger.debug("Batch embedding complete.")

    # Iterate through entries and their corresponding pre-computed embeddings
    for i, (entry, embedding) in enumerate(zip(state.filtered_results.entries, all_embeddings)):
        logger.trace(f"Processing entry {i + 1}/{len(state.filtered_results.entries)}: {entry.name}")
        await create_log_entry(
            state.db_session,
            current_time,
            entry.name,
            entry.description,
            entry.location,
            entry.landmarks,
            entry.confidence,
            entry.formatted_description,
            embedding
        )

    logger.debug("Save analysis complete")
    logger.trace("Exiting save_analysis function")
    return {
        "save_status": True,
        "analyses_buffer": state.formatted_analyses[-10:]
    }
