import pprint

from logging_config import get_logger

logger = get_logger(__name__)


def format_dict(d: dict) -> str:
    """Pretty print a dictionary and return its string representation.

    Args:
        d: Dictionary to pretty print

    Returns:
        str: Formatted string representation of the dictionary
    """
    pp = pprint.PrettyPrinter(indent=2, sort_dicts=False)
    return f"\n```\n{pp.pformat(d)}\n```"
