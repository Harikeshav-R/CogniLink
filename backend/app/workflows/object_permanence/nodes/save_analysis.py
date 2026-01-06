import time

from loguru import logger

from app.crud.object_permanence import create_log_entry
from app.shared.model_factory import init_embeddings_model
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState


async def save_analysis(state: ObjectPermanenceWorkflowState) -> dict:
    """
    Saves analysis data to the database by processing unique objects and their associated
    descriptions from the given workflow state.

    This function verifies the presence of unique objects and a valid database session
    before attempting to save data. It filters out invalid descriptions, generates
    embeddings for valid descriptions, and logs the results to persistent storage.

    :param state: The workflow state containing unique objects, generated descriptions, and
        a database session.
    :type state: ObjectPermanenceWorkflowState
    :return: A dictionary containing the final status of the storage operation.
    :rtype: dict
    """
    if not state.unique_objects:
        return {"final_storage_status": "Skipped (No new objects)"}

    if not state.db_session:
        logger.error("Database session not found in workflow state. Skipping save.")
        return {"final_storage_status": "Failed (No DB session)"}

    current_time = time.time()

    embeddings_model = init_embeddings_model()

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
