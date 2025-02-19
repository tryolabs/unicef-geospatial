import json

import geemap.foliumap as geemap
from ee.deserializer import fromJSON
from ee.errormargin import ErrorMargin
from ee.feature import Feature
from ee.featurecollection import FeatureCollection
from ee.image import Image
from langchain.tools import tool
from logging_config import get_logger

INTERSECTION_PATH = "data/intersection.html"


@tool
def intersect_feature_collection(
    paths_to_feature_collections: list[str],
) -> str:
    """Intersect a list of feature collections and return the resulting feature collection.

    Args:
        paths_to_feature_collections: List of paths to the feature collections to intersect

    Returns:
        FeatureCollection: Intersection of the input feature collections
    """
    logger = get_logger(__name__)
    logger.info("Intersecting feature collections: %s", paths_to_feature_collections)

    if len(paths_to_feature_collections) == 0:
        raise ValueError("No feature collections provided")

    intersection = load_vector_data(paths_to_feature_collections[0])
    for path in paths_to_feature_collections[1:]:
        new_feature = load_vector_data(path)
        intersection = intersection.map(lambda f: intersect_feature(f, new_feature))

    save_vector_data(INTERSECTION_PATH, intersection)
    return INTERSECTION_PATH


def intersect_feature(feature_1: Feature, feature_2: Feature) -> Feature:
    """Intersect a feature with a feature collection.

    Computes the geometric intersection between a feature and a feature collection,
    preserving the properties of the input feature.

    Args:
        feature: The feature to intersect
        feature_collection: The feature collection to intersect with

    Returns:
        Feature: A new feature representing the intersection, with properties copied from
                the input feature
    """
    intersected = feature_1.geometry().intersection(
        feature_2.geometry(), ErrorMargin(100)
    )
    return Feature(intersected).copyProperties(feature_1)


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


def save_vector_data(path: str, vector_data: FeatureCollection) -> None:
    """Save a vector data to a file."""
    logger = get_logger(__name__)
    logger.info("Saving vector data to %s", path)
    serialized_vector_data = vector_data.serialize()
    with open(path, "w") as f:
        logger.info("Writing vector data to %s", path)
        json.dump(serialized_vector_data, f)


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
