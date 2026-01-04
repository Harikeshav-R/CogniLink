from langchain.chat_models import init_chat_model

from app.core.config import Config


def init_google_genai_chat_model(model: str, api_key: str):
    return init_chat_model(
        model=model,
        model_provider=Config.GEMINI_PROVIDER,
        api_key=api_key
    )


def init_pollinations_chat_model(model: str, api_key: str):
    return init_chat_model(
        model=model,
        model_provider=Config.POLLINATIONS_PROVIDER,
        api_key=api_key,
        base_url=Config.POLLINATIONS_ENDPOINT
    )
