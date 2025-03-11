from logging_config import get_logger
from utils.types import DatasetMetadata

PATH_TO_RIVER_FLOOD = "unicef_geospatial/data/river_flood_image.json"

logger = get_logger(__name__)


def get_river_flood_metadata() -> DatasetMetadata:
    """Get the river flood metadata.

    Returns:
        dict[str, str]: A dictionary containing:
            - path_to_image: Path to where to save the river flood image file
            - input_arguments: Input arguments for the tool
            - asset_id: Asset ID of the river flood image
            - mosaic: Whether to mosaic the image
    """
    logger.info("Getting river flood information")
    metadata = DatasetMetadata(
        path_to_image=PATH_TO_RIVER_FLOOD,
        asset_id="projects/unicef-ccri/assets/river_flood_r10",
        mosaic=True,
        threshold=0.5,
        greater_than=True,
    )
    return metadata
