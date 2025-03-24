import json

import geemap.foliumap as geemap
from ee.deserializer import fromJSON
from ee.featurecollection import FeatureCollection
from ee.image import Image
from logging_config import get_logger
from utils.constants import PATH_TO_MAP

logger = get_logger(__name__)


def image_to_html(
    image: Image,
    vector_data: FeatureCollection,
    name: str = "",
    vis_params: dict = {},
    center: bool = True,
) -> str:
    """Converts an Earth Engine image to an HTML string."""
    logger.info("Converting image to HTML")
    demographic_map = geemap.Map()
    clipped_image = image.clip(vector_data)
    demographic_map.add_layer(clipped_image, vis_params, name)
    if center:
        demographic_map.center_object(vector_data, max_error=0.1)
    demographic_map.to_html(PATH_TO_MAP)
    return PATH_TO_MAP


def save_vector_data(path: str, vector_data: FeatureCollection | Image) -> None:
    """Save a vector data to a file."""
    logger = get_logger(__name__)
    logger.info("Saving vector data to %s", path)
    serialized_vector_data = vector_data.serialize()
    with open(path, "w") as f:
        logger.info("Writing vector data to %s", path)
        json.dump(serialized_vector_data, f)


def load_vector_data(path_to_vector_data: str) -> FeatureCollection | Image:
    """Load vector data from a JSON file and convert to Earth Engine FeatureCollection or Image.

    Args:
        path_to_vector_data: Path to the JSON file containing the vector data

    Returns:
        Either an Earth Engine FeatureCollection or Image object
    """
    try:
        with open(path_to_vector_data, "r") as f:
            logger.info(f"Going to load vector data from {path_to_vector_data}")
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
