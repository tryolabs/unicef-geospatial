import geemap.foliumap as geemap
from ee.deserializer import fromJSON
from ee.featurecollection import FeatureCollection
from ee.image import Image
from logging_config import get_logger


def image_to_html(
    image: Image,
    name: str = "",
    vis_params: dict = {},
    center: bool = False,
) -> str:
    """Converts an Earth Engine image to an HTML string."""
    demographic_map = geemap.Map()
    demographic_map.add_layer(image, vis_params, name)
    if center:
        demographic_map.center_object(image)
    html = demographic_map.to_html()
    if html is None:
        error_msg = "Failed to generate map"
        raise ValueError(error_msg)

    return html


def save_html(path: str, html: str) -> None:
    """Save an HTML string to a file."""
    logger = get_logger(__name__)
    logger.info("Saving map to %s", path)
    with open(path, "w") as f:
        logger.info("Writing map to %s", path)
        f.write(html)


def load_vector_data(path_to_vector_data: str) -> FeatureCollection:
    """Load vector data from a JSON file and convert to Earth Engine FeatureCollection.

    Reads a JSON file containing vector data (e.g. polygons, points) and converts it
    to an Earth Engine FeatureCollection object that can be used for geospatial analysis.

    Args:
        path_to_vector_data: Path to the JSON file containing the vector data

    Returns:
        FeatureCollection: Earth Engine FeatureCollection object containing the vector data
    """
    try:
        # Convert the dictionary to FeatureCollection
        logger = get_logger(__name__)
        with open(path_to_vector_data, "r") as f:
            logger.info(f"Going to load vector data from {path_to_vector_data}")
            json_value = eval(f.read())
            zone_vector = fromJSON(json_value)

        zone_vector = zone_vector.getInfo()
        zone_vector = FeatureCollection(zone_vector)
        return zone_vector
    except Exception as e:
        logger.error(f"Error in vector conversion: {str(e)}")
        raise e
