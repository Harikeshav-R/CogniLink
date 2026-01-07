from datetime import datetime

from app.core.db import get_session
from app.crud.object_permanence import read_object_permanence_entries_by_vector_search
from app.shared.model_factory import init_embeddings_model
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, DbQueryOutput


async def retrieve_matching_objects(state: ObjectPermanenceWorkflowState) -> dict:
    embeddings_model = init_embeddings_model()
    query_vector = await embeddings_model.aembed_query(state.query)

    async with get_session() as db_session:
        search_results = await read_object_permanence_entries_by_vector_search(db_session, query_vector,
                                                                               state.number_of_entries_to_query)

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
