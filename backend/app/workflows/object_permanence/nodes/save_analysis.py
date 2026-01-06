import time

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from loguru import logger

from app.core.config import Config
from app.crud.object_permanence import create_log_entry
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState


async def save_analysis(state: ObjectPermanenceWorkflowState) -> dict:
    if not state.unique_objects:
        return {"final_storage_status": "Skipped (No new objects)"}

    if not state.db_session:
        logger.error("Database session not found in workflow state. Skipping save.")
        return {"final_storage_status": "Failed (No DB session)"}

    current_time = time.time()

    logger.debug("Initializing embedding model...")
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model=Config.GEMINI_EMBEDDING_MODEL,
        google_api_key=Config.GEMINI_API_KEY,
        vertexai=False
    )
    logger.debug("Embedding model initialized.")

    # Filter out any entries where a description wasn't generated
    valid_indices = [i for i, desc in enumerate(state.generated_descriptions) if desc]
    if not valid_indices:
        logger.warning("No valid descriptions were generated. Skipping save.")
        return {"final_storage_status": "Skipped (No valid descriptions)"}

    valid_objects = [state.unique_objects[i] for i in valid_indices]
    valid_descriptions = [state.generated_descriptions[i] for i in valid_indices]

    logger.debug(f"Batch embedding {len(valid_objects)} entries...")
    # embed_documents handles batching internally
    all_embeddings = await embeddings_model.aembed_documents(valid_descriptions)
    logger.debug("Batch embedding complete.")

    # Iterate through entries and their corresponding pre-computed embeddings
    for entry, description, embedding in zip(valid_objects, valid_descriptions, all_embeddings):
        await create_log_entry(
            state.db_session,
            current_time,
            entry.object_name,
            description,
            embedding,
        )

    logger.debug("Save analysis complete")
    logger.trace("Exiting save_analysis function")
    return {
        "final_storage_status": "Success",
    }
