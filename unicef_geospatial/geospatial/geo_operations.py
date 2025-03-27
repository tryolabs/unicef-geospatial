import ee
from ee.errormargin import ErrorMargin
from ee.feature import Feature
from ee.image import Image
from ee.imagecollection import ImageCollection
from ee.reducer import Reducer
from geospatial.earth_engine import get_dataset_metadata
from geospatial.io import image_to_html, load_vector_data, save_vector_data
from langchain.tools import tool
from logging_config import get_logger
from utils.types import ALL_DATASETS, REDUCERS

INTERSECTION_PATH = "unicef_geospatial/data/intersection.json"
logger = get_logger(__name__)


@tool
def get_dataset_image_and_metadata(
    dataset: ALL_DATASETS,
) -> dict[str, str]:
    """Get an image from Earth Engine and save it as a vector data.

    Args:
        dataset: The dataset to get the image and metadata for

    Returns:
        A dictionary containing the metadata for the dataset:
            - path_to_image: Path to where the image is saved
            - description: Description of the dataset
            - threshold: Threshold value for filtering (if applicable)
            - input_arguments: Input arguments for the tool

    """
    metadata = get_dataset_metadata(dataset)
    logger.info(f"Getting image from {metadata.asset_id}")
    if metadata.mosaic:
        image = ImageCollection(metadata.asset_id).mosaic()
    else:
        image = Image(metadata.asset_id)
        if dataset == ALL_DATASETS.AGRICULTURAL_DROUGHT:
            # TODO: maybe this image should be preprocessed
            image = image.updateMask(image.lte(100))

    save_vector_data(metadata.path_to_image, image)
    return {
        "path_to_image": metadata.path_to_image,
        "description": metadata.description,
        "threshold": metadata.threshold,
        "input_arguments": {
            "dataset": dataset,
        },
    }


@tool
def mask_image(path_to_image: str, path_to_mask: str) -> dict[str, str]:
    """Mask an Earth Engine image based on a mask.

    A mask is a binary image that is used to mask the image.

    Args:
        path_to_image: Path to the JSON file containing the Earth Engine image
        path_to_mask: Path to the JSON file containing the Earth Engine mask

    Returns:
        dict: A dictionary containing:
            - path_to_image: Path to the saved masked image file
            - input_arguments: The original input arguments used for the operation
    """
    image = load_vector_data(path_to_image)
    mask = load_vector_data(path_to_mask)
    if not isinstance(image, Image):
        raise TypeError(
            f"Expected an Earth Engine Image object, but got {type(image).__name__}. "
            f"Please provide a valid image path."
        )
    if not isinstance(mask, Image):
        raise TypeError(
            f"Expected an Earth Engine Image object, but got {type(mask).__name__}. "
            f"Please provide a valid mask path."
        )
    masked_image = image.updateMask(mask)
    path_to_masked_image = path_to_image.replace(".json", "_masked.json")
    save_vector_data(path_to_masked_image, masked_image)
    return {
        "path_to_image": path_to_masked_image,
        "input_arguments": {
            "path_to_image": path_to_image,
            "path_to_mask": path_to_mask,
        },
    }


@tool
def filter_image_by_threshold(
    path_to_image: str, threshold: float, greater_than: bool = True
) -> dict[str, str | dict]:
    """Mask an Earth Engine image based on a threshold value.

    This function applies a threshold filter to an image.
    The result is a binary image where the values are either 0 or 1.

    Args:
        path_to_image: Path to the JSON file containing the Earth Engine image
        threshold: Numeric value to use as the threshold for filtering
        greater_than: If True, keep values greater than threshold;
            if False, keep values less than threshold

    Returns:
        dict: A dictionary containing:
            - path_to_image: Path to the saved masked image file
            - input_arguments: The original input arguments used for the operation

    Raises:
        TypeError: If the loaded data is not an Earth Engine Image object
    """
    logger.info(f"Filtering image {path_to_image} by threshold: {threshold}")
    image = load_vector_data(path_to_image)
    if not isinstance(image, Image):
        raise TypeError(
            f"Expected an Earth Engine Image object, but got {type(image).__name__}. "
            f"Please provide a valid image path."
        )
    # Create a mask where values are less than threshold
    threshold_ee = ee.Number(threshold)
    filtered_mask = image.gt(threshold_ee) if greater_than else image.lt(threshold_ee)
    # Apply the mask to the original image

    path_to_filtered_vector_data = path_to_image.replace(".json", "_filtered.json")

    save_vector_data(path_to_filtered_vector_data, filtered_mask)
    return {
        "path_to_image": path_to_filtered_vector_data,
        "input_arguments": {
            "path_to_image": path_to_image,
            "threshold": threshold,
            "greater_than": greater_than,
        },
    }


@tool
def intersect_feature_collection(
    paths_to_feature_collections: list[str],
) -> str:
    """Intersect a list of feature collections and return the resulting data.

    It is not possible to intersect images, just vector data.

    Args:
        paths_to_feature_collections: List of paths to the feature collections/images to intersect

    Returns:
        dict: Dictionary containing paths to the intersection result and HTML visualization
    """
    logger.info("Intersecting data: %s", paths_to_feature_collections)

    if len(paths_to_feature_collections) == 0:
        raise ValueError("No feature collections provided")

    intersection = load_vector_data(paths_to_feature_collections[0])
    if isinstance(intersection, Image):
        # if images are intersected, the values of each are changed
        # only feature collections can be intersected
        raise ValueError("Image cannot be intersected")

    for path in paths_to_feature_collections[1:]:
        new_data = load_vector_data(path)
        if isinstance(new_data, Image):
            raise ValueError("Image cannot be intersected")
        intersection = intersection.map(lambda f: intersect_feature(f, new_data))

    save_vector_data(INTERSECTION_PATH, intersection)
    return {
        "path_to_vector_data": INTERSECTION_PATH,
        "input_arguments": {
            "paths_to_feature_collections": paths_to_feature_collections
        },
    }


@tool
def reduce_image(
    path_to_image: str,
    path_to_geometry: str,
    reducer: REDUCERS,
    scale: int = 100,
) -> dict:
    """Reduce an image by applying a reducer to its pixels.

    Args:
        path_to_image: The path to the image to reduce
        path_to_geometry: The path to the geometry to reduce the image to
        reducer: The reducer to apply
        scale: The scale of the image. It should be 100 unless otherwise specified.

    Returns:
        dict: A dictionary containing the reduced value
    """
    logger.info(f"Reducing image with {reducer}")
    image = load_vector_data(path_to_image)
    feature_collection = load_vector_data(path_to_geometry)
    reduced = image.reduceRegions(
        reducer=getattr(Reducer, reducer)(),
        collection=feature_collection,
        scale=scale,
        crs="EPSG:4326",
    )
    stats = reduced.getInfo()

    total_sum = 0
    for feature in stats["features"]:
        total_sum += feature["properties"]["sum"]
    logger.info(f"Reduced image with {reducer} to {total_sum}")

    return {
        "total_sum": total_sum,
        "input_arguments": {
            "path_to_image": path_to_image,
            "path_to_geometry": path_to_geometry,
            "reducer": reducer,
            "scale": scale,
        },
    }


@tool
def build_map(
    path_to_image: str,
    path_to_vector_data: str,
    name: str = "",
) -> dict:
    """Build a map from an image and vector data and save it to an HTML file.

    Creates an interactive map by overlaying an Earth Engine image on top of vector data
    (e.g. administrative boundaries). The map is saved as an HTML file that can be viewed
    in a web browser.

    Args:
        path_to_image: Path to the Earth Engine image file to display on the map
        path_to_vector_data: Path to the vector data file (e.g. GeoJSON) defining the
            boundaries to overlay the image on
        name: The name of the map
        center: Whether to center the map on the vector data

    Returns:
        dict: A dictionary containing the path to the saved HTML map file under the key
            'path_to_map'
    """
    logger.info(f"Building map with {path_to_image} and {path_to_vector_data}")
    vector_data = load_vector_data(path_to_vector_data)
    image = load_vector_data(path_to_image)
    return {
        "path_to_map": image_to_html(
            image=image, vector_data=vector_data, name=name, center=True
        ),
        "input_arguments": {
            "path_to_image": path_to_image,
            "path_to_vector_data": path_to_vector_data,
            "name": name,
        },
    }


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
