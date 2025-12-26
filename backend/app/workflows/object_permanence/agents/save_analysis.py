import time

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import Config
from app.crud.object_permanence import create_log_entry
from app.workflows.object_permanence.state import State


def get_embeddings(text: str) -> list[float]:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=Config.GEMINI_API_KEY)
    vector = embeddings.embed_query(text)

    return vector


def save_analysis(state: State) -> dict:
    if not state.filtered_results:
        return {}

    current_time = time.time()

    for entry in state.filtered_results.entries:
        embedding = get_embeddings(entry.content)
        create_log_entry(
            state.db_session,
            entry.content,
            embedding,
            current_time,
            entry.object_name
        )

    return {"save_status": True}
