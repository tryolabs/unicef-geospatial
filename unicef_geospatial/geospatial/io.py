import json
import os

import geemap.foliumap as geemap
from ee.deserializer import fromJSON
from ee.featurecollection import FeatureCollection
from ee.image import Image
from logging_config import get_logger
from utils.constants import MAP_FILENAME

logger = get_logger(__name__)


def image_to_html(
    images: list[Image],
    vector_data: FeatureCollection,
    temp_dir: str = "",
    names: list[str] = [],
    vis_params: dict = {},
    center: bool = True,
) -> str:
    """Converts an Earth Engine image to an HTML string."""
    demographic_map = geemap.Map()
    for i, image in enumerate(images):
        logger.info(f"Adding layer {names[i]}")
        clipped_image = image.clip(vector_data)
        demographic_map.add_layer(clipped_image, vis_params, names[i])
    if center:
        demographic_map.center_object(vector_data, max_error=0.1)
    demographic_map.to_html(os.path.join(temp_dir, MAP_FILENAME))
    return MAP_FILENAME


def save_ee_object(path: str, vector_data: FeatureCollection | Image) -> None:
    """Save a vector data to a file."""
    logger = get_logger(__name__)
    logger.info("Saving vector data to %s", path)
    serialized_vector_data = vector_data.serialize()
    with open(path, "w") as f:
        logger.info("Writing vector data to %s", path)
        json.dump(serialized_vector_data, f)


def load_vector_data(feature_collection_filename: str) -> FeatureCollection | Image:
    """Load vector data from a JSON file and convert to Earth Engine FeatureCollection or Image.

    Args:
        feature_collection_filename: Path to the JSON file containing the vector data

    Returns:
        Either an Earth Engine FeatureCollection or Image object
    """
    try:
        logger.info(f"Going to load vector data from {feature_collection_filename}")
        with open(feature_collection_filename, "r") as f:
            vector_data = eval(f.read())
            vector_data = fromJSON(vector_data)
        # Get the info without converting to Python dict
        if isinstance(vector_data, Image):
            logger.info("Vector data is an image")
            return vector_data
        elif isinstance(vector_data, FeatureCollection):
            logger.info("Vector data is a feature collection")
            return vector_data
        else:
            if vector_data.getInfo().get("type") == "Image":
                logger.info("Vector data is an image")
                return Image(vector_data)
            elif vector_data.getInfo().get("type") == "FeatureCollection":
                logger.info("Vector data is a feature collection")
                return FeatureCollection(vector_data)
            raise ValueError(f"Unknown vector data type: {type(vector_data)}")

    except Exception as e:
        logger.error(f"Error in vector conversion: {str(e)}")
        raise e
