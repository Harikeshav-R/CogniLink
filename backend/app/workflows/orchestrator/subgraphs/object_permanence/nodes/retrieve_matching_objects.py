from datetime import datetime
from loguru import logger
from app.core.db import get_session
from app.crud.object_permanence import read_object_permanence_entries_by_vector_search
from app.shared.model_factory import init_embeddings_model
from app.workflows.orchestrator.subgraphs.object_permanence.schemas import ObjectPermanenceWorkflowState, DbQueryOutput


async def retrieve_matching_objects(state: ObjectPermanenceWorkflowState) -> dict:
    """
    Retrieve matching objects based on query and return results in a structured format.

    This function asynchronously processes a query to find matching objects by using an
    embeddings model and a database session. It computes a query vector, performs vector
    search for relevant entries, sorts the results by timestamp, and formats the result
    into a dictionary. If no matching entries are found, it indicates so in the output.

    :param state: Current workflow state containing the query.
    :type state: ObjectPermanenceWorkflowState

    :return: A dictionary containing the search result with a flag indicating if matching
        entries were found, and the list of matching entries (sorted and formatted) if found.
    :rtype: dict
    """
    logger.info("Retrieving matching objects for the object permanence workflow.")
    logger.debug(f"Current state: {state}")

    logger.trace("Initializing embeddings model.")
    embeddings_model = init_embeddings_model()
    logger.trace("Embeddings model initialized.")

    logger.debug(f"Generating query vector for query: '{state.query}'")
    query_vector = await embeddings_model.aembed_query(state.query)
    logger.debug("Query vector generated successfully.")
    logger.trace(f"Query vector: {query_vector[:5]}... (first 5 dimensions)")

    async with get_session() as db_session:
        logger.debug("Executing vector search for matching entries.")
        search_results = await read_object_permanence_entries_by_vector_search(db_session, query_vector)
        logger.debug(f"Found {len(search_results)} matching entries from the database.")

        if not search_results:
            logger.warning("No matching entries found.")
            return {
                "found_matching_entries": False
            }

        logger.trace("Sorting search results by timestamp in descending order.")
        search_results.sort(key=lambda x: x.timestamp, reverse=True)
        logger.trace("Search results sorted.")

        output: list[DbQueryOutput] = []

        logger.trace("Formatting search results into DbQueryOutput objects.")
        for result in search_results:
            formatted_timestamp = datetime.fromtimestamp(result.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            output.append(
                DbQueryOutput(
                    object_name=result.object_name,
                    description=result.description,
                    timestamp=formatted_timestamp
                )
            )
        logger.trace("All results formatted.")

        final_output = {
            "found_matching_entries": True,
            "matching_entries": output
        }
        logger.success("Matching objects retrieved and formatted successfully.")
        logger.trace(f"Returning final output: {final_output}")
        return final_output

