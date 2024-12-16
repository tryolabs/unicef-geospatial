from unicef_geospatial.logging_config import get_logger

logger = get_logger(__name__)


def print_stream(stream: list) -> None:
    """Print messages from a stream of LangGraph agent responses.

    Args:
        stream: List of agent response messages to print
    """
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            logger.info(message)
        else:
            message.pretty_print()
