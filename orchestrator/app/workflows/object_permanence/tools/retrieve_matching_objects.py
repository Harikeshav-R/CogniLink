from datetime import datetime

from langchain.tools import tool

from app.core.db import get_session
from app.crud.object_permanence import read_object_permanence_entries_by_vector_search
from app.shared.model_factory import init_embeddings_model


@tool
async def retrieve_matching_objects(query: str) -> str:
    """
    Finds object entries in the database matching the specified query.

    This function performs a vector search using embeddings generated from the input query
    to retrieve matching object permanence entries from the database. The results are sorted
    by timestamp in descending order before being presented in a structured text format.

    :param query: The search query string used to find matching object entries.
    :type query: str
    :return: A structured string list of matching database entries sorted from newest to oldest
             or a message indicating no match was found.
    :rtype: str
    """
    embeddings_model = init_embeddings_model()
    query_vector = await embeddings_model.aembed_query(query)

    async with get_session() as db_session:
        search_results = await read_object_permanence_entries_by_vector_search(db_session, query_vector)

        if not search_results:
            return "I could not find any records matching that object in the database."

        search_results.sort(key=lambda x: x.timestamp, reverse=True)

        output: list[str] = []

        for result in search_results:
            output.append(
                f"""
                Object: {result.object_name}
                Description: {result.description}
                Timestamp: {datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
                """
            )

        return \
            f"""
            Here is a list of the entries in the database (sorted from newest to oldest) matching the object you requested:
            {"\n".join(output)}
            """
