import ee
from langchain.chat_models.base import BaseChatModel
from langchain_cohere import ChatCohere


def initialize_earth_engine(project: str) -> None:
    """Initialize the Earth Engine API."""
    ee.Authenticate()
    ee.Initialize(project=project)


def get_llm(temperature: float) -> BaseChatModel:
    """Get the LLM model."""
    return ChatCohere(temperature=temperature)
