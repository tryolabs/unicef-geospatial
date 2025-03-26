from logging_config import get_logger
from utils.constants import PATH_TO_STORM, STORM_DATASET
from utils.types import DatasetMetadata

logger = get_logger(__name__)


def get_storm_metadata() -> DatasetMetadata:
    """Get the storm metadata."""
    logger.info("Getting storm metadata")
    metadata = DatasetMetadata(
        path_to_image=PATH_TO_STORM,
        asset_id=STORM_DATASET,
        description="Wind speed in km/h",
        mosaic=True,
        threshold=17.5,
        greater_than=True,
    )
    return metadata
