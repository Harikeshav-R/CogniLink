import json
import time

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from loguru import logger
from pydantic import RootModel

from app.core.config import Config
from app.crud.object_permanence import create_log_entry
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.state import ObjectPermanenceState, ObjectPermanenceObject


async def format_and_save_state(state: ObjectPermanenceState) -> dict:
    logger.trace("Entering format_and_save_state function")

    # Part 1: Format the analysis
    logger.debug("Initializing chat model for analyses formatting...")
    format_model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
        Config.POLLINATIONS_API_KEY
    )
    logger.debug("Chat model initialized.")

    logger.debug("Creating agent for analyses formatting...")
    format_agent = create_agent(
        model=format_model,
        response_format=RootModel[list[ObjectPermanenceObject]],
        system_prompt=SystemMessage(
            content=Prompts.FORMAT_ANALYSES_AGENT
        ),
    )
    logger.debug("Agent created.")

    format_result = await format_agent.ainvoke(
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": Prompts.FORMAT_ANALYSES_AGENT
                },
                {
                    "type": "text",
                    "text": "Here is your list of analyses to format:"
                },
                {
                    "type": "text",
                    "text": json.dumps(
                        [obj.model_dump() for obj in state.current_analysis],
                        indent=2
                    )
                }
            ]
        )
    )
    logger.debug("Agent invocation for formatting complete.")
    formatted_analyses: list[ObjectPermanenceObject] = format_result["structured_response"]

    # Part 2: Save the formatted analysis
    current_time = time.time()

    valid_analyses = [
        entry for entry in formatted_analyses if entry.formatted_description
    ]

    if not valid_analyses:
        logger.warning("No valid formatted descriptions to save.")
        return {"save_status": False}

    contents = [entry.formatted_description for entry in valid_analyses]
    logger.debug(f"Extracted {len(contents)} content strings for embedding.")

    logger.debug("Initializing embedding model...")
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model=Config.GEMINI_EMBEDDING_MODEL,
        google_api_key=Config.GEMINI_API_KEY,
        vertexai=False
    )
    logger.debug("Embedding model initialized.")

    logger.debug(f"Batch embedding {len(contents)} entries...")
    all_embeddings = await embeddings_model.aembed_documents(contents)
    logger.debug("Batch embedding complete.")

    for entry, embedding in zip(valid_analyses, all_embeddings):
        logger.trace(f"Processing entry: {entry.name}")
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
    logger.trace("Exiting format_and_save_state function")
    return {"save_status": True}
