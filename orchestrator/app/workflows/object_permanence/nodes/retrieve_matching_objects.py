from datetime import datetime

from app.core.db import get_session
from app.crud.object_permanence import read_object_permanence_entries_by_vector_search
from app.shared.model_factory import init_embeddings_model
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, DbQueryOutput


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
    embeddings_model = init_embeddings_model()
    query_vector = await embeddings_model.aembed_query(state.query)

    async with get_session() as db_session:
        search_results = await read_object_permanence_entries_by_vector_search(db_session, query_vector)

        if not search_results:
            return {
                "found_matching_entries": False
            }

        search_results.sort(key=lambda x: x.timestamp, reverse=True)

        output: list[DbQueryOutput] = []

        for result in search_results:
            output.append(
                DbQueryOutput(
                    object_name=result.object_name,
                    description=result.description,
                    timestamp=datetime.fromtimestamp(result.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                )
            )

        return {
            "found_matching_entries": True,
            "matching_entries": output
        }
