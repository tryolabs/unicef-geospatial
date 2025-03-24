from logging_config import get_logger
from utils.constants import (
    COASTAL_FLOOD_DATASET,
    PATH_TO_COASTAL_FLOOD,
    PATH_TO_PLUVIAL_FLOOD,
    PATH_TO_RIVER_FLOOD,
    PLUVIAL_FLOOD_DATASET,
    RIVER_FLOOD_DATASET,
)
from utils.types import DatasetMetadata

logger = get_logger(__name__)


def get_river_flood_metadata() -> DatasetMetadata:
    """Get the river flood metadata.

    Returns:
        DatasetMetadata: The river flood metadata
    """
    logger.info("Getting river flood information")
    metadata = DatasetMetadata(
        path_to_image=PATH_TO_RIVER_FLOOD,
        asset_id=RIVER_FLOOD_DATASET,
        description="Zones of river flood. The value indicates the depth in meters.",
        mosaic=True,
        threshold=0.01,
        greater_than=True,
    )
    return metadata


def get_coastal_flood_metadata() -> DatasetMetadata:
    """Get the coastal flood metadata.

    Returns:
        DatasetMetadata: The coastal flood metadata
    """
    logger.info("Getting coastal flood information")
    metadata = DatasetMetadata(
        path_to_image=PATH_TO_COASTAL_FLOOD,
        asset_id=COASTAL_FLOOD_DATASET,
        description="Zones of coastal flood. The value is 1 if the zone is flooded, 0 otherwise.",
        mosaic=True,
        threshold=0,
        greater_than=True,
    )
    return metadata


def get_pluvial_flood_metadata() -> DatasetMetadata:
    """Get the pluvial flood metadata.

    Returns:
        DatasetMetadata: The pluvial flood metadata
    """
    logger.info("Getting pluvial flood information")
    metadata = DatasetMetadata(
        path_to_image=PATH_TO_PLUVIAL_FLOOD,
        asset_id=PLUVIAL_FLOOD_DATASET,
        description="Zones of pluvial flood. The value indicates the depth in meters.",
        mosaic=False,
        threshold=3,  # TODO: TBD the value
        greater_than=True,
    )
    return metadata
