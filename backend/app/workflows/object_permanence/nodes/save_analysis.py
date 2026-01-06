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
    logger.trace("Entering 'save_analysis' node.")
    if not state.unique_objects:
        logger.warning("No unique objects in state. Skipping save.")
        return {"final_storage_status": "Skipped (No new objects)"}

    if not state.db_session:
        logger.error("Database session not found in workflow state. Cannot save analysis.")
        return {"final_storage_status": "Failed (No DB session)"}

    logger.debug(f"Found {len(state.unique_objects)} unique objects to process for saving.")
    current_time = time.time()
    logger.trace(f"Using timestamp for all entries: {current_time}")

    logger.debug("Initializing embeddings model...")
    embeddings_model = init_embeddings_model()
    logger.trace("Embeddings model initialized.")

    # Filter out any entries where a description wasn't generated
    logger.debug("Filtering objects with valid, non-empty descriptions.")
    valid_indices = [i for i, desc in enumerate(state.generated_descriptions) if desc]
    if not valid_indices:
        logger.warning("No valid descriptions were generated for any unique objects. Nothing to save.")
        return {"final_storage_status": "Skipped (No valid descriptions)"}

    valid_objects = [state.unique_objects[i] for i in valid_indices]
    valid_descriptions = [state.generated_descriptions[i] for i in valid_indices]
    logger.info(f"Found {len(valid_objects)} objects with valid descriptions to be saved.")
    logger.trace(f"Valid descriptions: {valid_descriptions}")

    logger.debug(f"Generating batch embeddings for {len(valid_descriptions)} descriptions...")
    # embed_documents handles batching internally
    all_embeddings = await embeddings_model.aembed_documents(valid_descriptions)
    logger.debug("Batch embedding generation complete.")
    logger.trace(f"Generated {len(all_embeddings)} embeddings.")

    # Iterate through entries and their corresponding pre-computed embeddings
    logger.debug(f"Iterating through {len(valid_objects)} objects to create log entries in the database.")
    for i, (entry, description, embedding) in enumerate(zip(valid_objects, valid_descriptions, all_embeddings)):
        logger.trace(f"Processing object {i+1}/{len(valid_objects)}: '{entry.object_name}'")
        try:
            await create_log_entry(
                state.db_session,
                current_time,
                entry.object_name,
                description,
                embedding,
            )
            logger.trace(f"Successfully created log entry for '{entry.object_name}'.")
        except Exception as e:
            logger.error(f"Failed to create log entry for object '{entry.object_name}'.", exc_info=True)
            # Continue to the next entry to attempt to save as much as possible
            continue

    logger.success(f"Save analysis complete. Processed {len(valid_objects)} objects.")
    logger.trace("Exiting 'save_analysis' node.")
    return {
        "final_storage_status": "Success",
    }
