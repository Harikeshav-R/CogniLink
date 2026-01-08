import json

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.core.config import Config
from app.shared.model_factory import init_pollinations_chat_model
from app.workflows.object_permanence.prompts import Prompts
from app.workflows.object_permanence.schemas import ObjectPermanenceWorkflowState, GenerateAnswerOutput


async def generate_answer(state: ObjectPermanenceWorkflowState) -> dict:
    """
    Generates an answer based on the current state of an object permanence workflow.

    This function interacts with the LLM to process the messages sent by
    the user and return a structured response. It uses a predefined system prompt
    and a generated agent to invoke the workflow asynchronously. The result is
    a processed output in the form of an answer derived from the user's input and
    the matching entries.

    :param state: An instance of ObjectPermanenceWorkflowState representing the
        current state of the workflow and the matching entries that should be
        included in the response.
    :type state: ObjectPermanenceWorkflowState
    :return: A dictionary containing the generated response derived from the answer
        provided by the structured response.
    :rtype: dict
    """
    model = init_pollinations_chat_model(
        Config.POLLINATIONS_SMART_MODEL,
        Config.POLLINATIONS_API_KEY
    )

    agent = create_agent(
        model=model,
        response_format=GenerateAnswerOutput,
        system_prompt=SystemMessage(
            content=Prompts.GENERATE_ANSWER
        ),
    )
    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Tool output:"},
                        {"type": "text", "text": "\n".join(
                            [json.dumps(entry.model_dump(), indent=2) for entry in state.matching_entries])}
                    ]
                }
            ]
        }
    )

    structured_response: GenerateAnswerOutput = response["structured_response"]
    return {"response": structured_response.answer}
