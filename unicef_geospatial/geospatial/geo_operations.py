import os

import ee
from ee.errormargin import ErrorMargin
from ee.feature import Feature
from ee.featurecollection import FeatureCollection
from ee.image import Image
from ee.imagecollection import ImageCollection
from ee.reducer import Reducer
from geospatial.earth_engine import get_dataset_metadata
from logging_config import get_logger
from utils.constants import INTERSECTION_FILENAME, UNION_FILENAME
from utils.io import image_to_html, load_vector_data, save_ee_object
from utils.schemas import REDUCERS, load_all_datasets_enum

logger = get_logger(__name__)


def get_dataset_image_and_metadata(
    dataset: load_all_datasets_enum(),
    temp_dir: str = "",
) -> dict[str, str]:
    """Get an image from Earth Engine and save it as a vector data.

    Args:
        dataset: The dataset to get the image and metadata for

    Returns:
        A dictionary containing the metadata for the dataset:
            - image_filename: Path to where the image is saved
            - description: Description of the dataset
            - threshold: Threshold value. If the values are above this threshold, the area is considered hazard zone.
            - input_arguments: Input arguments for the tool

    Use case:
        Retrieve a global agricultural drought dataset to analyze drought conditions:
        get_dataset_image_and_metadata(ALL_DATASETS.AGRICULTURAL_DROUGHT)

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    metadata = get_dataset_metadata(dataset)
    logger.info(f"Getting image from {metadata.asset_id}")
    if metadata.mosaic:
        image = ImageCollection(metadata.asset_id).mosaic()
    else:
        image = Image(metadata.asset_id)
        if dataset == load_all_datasets_enum().AGRICULTURAL_DROUGHT:
            # TODO: maybe this image should be preprocessed
            logger.info("Updating mask for agricultural drought")
            image = image.updateMask(image.lte(100))

    save_ee_object(os.path.join(temp_dir, metadata.image_filename), image)
    return {
        **metadata.model_dump(),
        "input_arguments": {
            "dataset": dataset,
        },
    }


def mask_image(
    image_filename: str, mask_image_filename: str, temp_dir: str = ""
) -> dict[str, str]:
    """Mask an Earth Engine image based on a mask.

    Masking an image means applying a binary filter to it, where pixels are retained only
    where the mask has non-zero values. This effectively "cuts out" or preserves only the
    areas of interest defined by the mask, while setting all other areas to no-data values.

    This is the operation used to intersect two images.

    The mask should be a binary image where:
    - Values of 1 (or non-zero) indicate areas to keep in the original image
    - Values of 0 indicate areas to mask out (set to no-data)

    This operation can only be used with images.

    Args:
        image_filename: Path to the JSON file containing the Earth Engine image
        mask_image_filename: Path to the JSON file containing the Earth Engine binary image mask.

    Returns:
        dict: A dictionary containing:
            - image_filename: Path to the saved masked image file
            - input_arguments: The original input arguments used for the operation

    Use case:
        Get the zone of exposed children to a hazard.
        mask_image(
            "child_population_data.json",
            "hazard_data.json",
        )

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    image = load_vector_data(os.path.join(temp_dir, image_filename))
    mask = load_vector_data(os.path.join(temp_dir, mask_image_filename))
    if not isinstance(image, Image):
        raise TypeError(
            f"Expected an Earth Engine Image object, but got {type(image).__name__}. "
            f"Please provide a valid image path. "
            f"{os.path.join(temp_dir, image_filename)} was invalid."
        )
    if not isinstance(mask, Image):
        raise TypeError(
            f"Expected an Earth Engine Image object, but got {type(mask).__name__}. "
            f"Please provide a valid mask path. "
            f"{os.path.join(temp_dir, mask_image_filename)} was invalid."
        )
    masked_image = image.updateMask(mask)
    path_to_masked_image = image_filename.replace(".json", "_masked.json")
    save_ee_object(os.path.join(temp_dir, path_to_masked_image), masked_image)
    return {
        "image_filename": path_to_masked_image,
        "input_arguments": {
            "image_filename": image_filename,
            "mask_image_filename": mask_image_filename,
        },
    }


def filter_image_by_threshold(
    image_filename: str, threshold: float, temp_dir: str = ""
) -> dict[str, str | dict]:
    """Filter an Earth Engine image based on a threshold value.

    This function applies a threshold filter to an image.
    The result is a binary image where the values are either 0 or 1.

    Args:
        image_filename: Path to the JSON file containing the Earth Engine image
        threshold: Numeric value to use as the threshold for filtering

    Returns:
        dict: A dictionary containing:
            - image_filename: Path to the saved filtered image file
            - input_arguments: The original input arguments used for the operation

    Raises:
        TypeError: If the loaded data is not an Earth Engine Image object

    Use case:
        Identify hazard areas with values above a threshold.
        filter_image_by_threshold("temperature_data.json", 35.0)

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    logger.info(f"Filtering image {image_filename} by threshold: {threshold}")
    image = load_vector_data(os.path.join(temp_dir, image_filename))
    if not isinstance(image, Image):
        raise TypeError(
            f"Expected an Earth Engine Image object, but got {type(image).__name__}. "
            f"Please provide a valid image path."
        )
    # Create a mask where values are less than threshold
    threshold_ee = ee.Number(threshold)
    filtered_mask = image.lt(threshold_ee) if threshold < 0 else image.gt(threshold_ee)

    path_to_filtered_vector_data = image_filename.replace(".json", "_filtered.json")
    save_ee_object(os.path.join(temp_dir, path_to_filtered_vector_data), filtered_mask)

    return {
        "image_filename": path_to_filtered_vector_data,
        "input_arguments": {
            "image_filename": image_filename,
            "threshold": threshold,
        },
    }


def union_binary_images(
    paths_to_binary_images: list[str], temp_dir: str = ""
) -> dict[str, str | dict]:
    """Union multiple binary images.

    This function loads binary images from the provided paths and performs
    a union operation, returning a new binary image where any of the input images
    have values of 1.

    Args:
        paths_to_binary_images: List of paths to the binary images to union.
            Each path should point to a valid Earth Engine Image saved as JSON.

    Returns:
        dict: A dictionary containing:
            - image_filename: Path to the saved union result
            - input_arguments: The original input arguments used for the operation

    Use case:
        Union two binary images to find areas that are either hazard zones.
        union_binary_images(["flood_zones.json", "drought_zones.json"])

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    logger.info("Unioning binary images: %s", paths_to_binary_images)
    if len(paths_to_binary_images) == 0:
        raise ValueError("No binary images provided")

    # Unmask the image to ensue non-data is treated as 0
    union = load_vector_data(os.path.join(temp_dir, paths_to_binary_images[0])).unmask(
        0
    )
    for path in paths_to_binary_images[1:]:
        new_data = load_vector_data(os.path.join(temp_dir, path)).unmask(0)
        union = union.Or(new_data)

    save_ee_object(os.path.join(temp_dir, UNION_FILENAME), union)
    return {
        "image_filename": UNION_FILENAME,
        "input_arguments": {"paths_to_binary_images": paths_to_binary_images},
    }


def intersect_binary_images(
    paths_to_binary_images: list[str], temp_dir: str = ""
) -> dict[str, str | dict]:
    """Intersect multiple binary images.

    This function loads binary images from the provided paths and performs
    an intersection operation, returning a new binary image where all the input images
    have values of 1.

    Args:
        paths_to_binary_images: List of paths to the binary images to intersect.
            Each path should point to a valid Earth Engine Image saved as JSON.

    Returns:
        dict: A dictionary containing:
            - image_filename: Path to the saved intersection result
            - input_arguments: The original input arguments used for the operation

    Use case:
        Intersect two binary images to find areas that are both hazard zones.
        intersect_binary_images(["flood_zones.json", "drought_zones.json"])

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    logger.info("Intersecting binary images: %s", paths_to_binary_images)
    if len(paths_to_binary_images) == 0:
        raise ValueError("No binary images provided")

    intersection = load_vector_data(os.path.join(temp_dir, paths_to_binary_images[0]))
    for path in paths_to_binary_images[1:]:
        new_data = load_vector_data(os.path.join(temp_dir, path))
        intersection = intersection.And(new_data)

    save_ee_object(os.path.join(temp_dir, INTERSECTION_FILENAME), intersection)
    return {
        "image_filename": INTERSECTION_FILENAME,
        "input_arguments": {"paths_to_binary_images": paths_to_binary_images},
    }


def intersect_feature_collections(
    paths_to_feature_collections: list[str], temp_dir: str = ""
) -> dict[str, str | dict]:
    """Perform a geometric intersection of multiple feature collections.

    This function loads feature collections from the provided paths and performs
    a geometric intersection operation, returning features that exist in all collections.

    Note: This operation only works with vector data (feature collections).
    Images cannot be intersected using this method.

    Args:
        paths_to_feature_collections: List of paths to the feature collections to intersect.
            Each path should point to a valid Earth Engine FeatureCollection saved as JSON.
            All inputs must be vector data (feature collections), not images.

    Returns:
        dict: A dictionary containing:
            - feature_collection_filename: Path to the saved intersection result
            - input_arguments: The original input arguments used for the operation

    Raises:
        ValueError: If no feature collections are provided or if any input is an Image

    Use case:
        Find areas that are both flood-prone and densely populated by intersecting flood hazard zones with population density data:
        intersect_feature_collections(["flood_zones.json", "high_population_areas.json"])

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    logger.info("Intersecting data: %s", paths_to_feature_collections)

    if len(paths_to_feature_collections) == 0:
        raise ValueError("No feature collections provided")

    intersection = load_vector_data(
        os.path.join(temp_dir, paths_to_feature_collections[0])
    )
    if isinstance(intersection, Image):
        # if images are intersected, the values of each are changed
        # only feature collections can be intersected
        raise ValueError("Image cannot be intersected")

    for path in paths_to_feature_collections[1:]:
        new_data = load_vector_data(os.path.join(temp_dir, path))
        if isinstance(new_data, Image):
            raise ValueError("Image cannot be intersected")
        intersection = intersection.map(lambda f: intersect_feature(f, new_data))

    save_ee_object(os.path.join(temp_dir, INTERSECTION_FILENAME), intersection)
    return {
        "feature_collection_filename": INTERSECTION_FILENAME,
        "input_arguments": {
            "paths_to_feature_collections": paths_to_feature_collections
        },
    }


def merge_feature_collections(
    paths_to_feature_collections: list[str], temp_dir: str = ""
) -> dict[str, str | dict]:
    """Merge multiple feature collections into a single combined collection.

    This function loads feature collections from the provided paths and merges them
    into a single feature collection containing all features from the input collections.

    Note: This operation only works with vector data (feature collections).
    Images cannot be merged using this method.

    Args:
        paths_to_feature_collections: List of paths to the feature collections to merge.
            Each path should point to a valid Earth Engine FeatureCollection saved as JSON.

    Returns:
        dict: A dictionary containing:
            - feature_collection_filename: Path to the saved merged result
            - input_arguments: The original input arguments used for the operation

    Raises:
        ValueError: If no feature collections are provided or if any input is an Image

    Use case:
        Combine different country areas into a single feature collection.
        merge_feature_collections(["uruguay.json", "argentina.json"])

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    logger.info("Unioning data: %s", paths_to_feature_collections)

    if len(paths_to_feature_collections) == 0:
        raise ValueError("No feature collections provided")

    union = load_vector_data(os.path.join(temp_dir, paths_to_feature_collections[0]))
    if isinstance(union, Image):
        raise ValueError("Image cannot be unioned")

    for path in paths_to_feature_collections[1:]:
        new_data = load_vector_data(os.path.join(temp_dir, path))
        if isinstance(new_data, Image):
            raise ValueError("Image cannot be unioned")
        union = union.merge(new_data).union()

    save_ee_object(os.path.join(temp_dir, UNION_FILENAME), union)
    return {
        "feature_collection_filename": UNION_FILENAME,
        "input_arguments": {
            "paths_to_feature_collections": paths_to_feature_collections
        },
    }


def reduce_image(
    image_filename: str,
    feature_collection_filename: str,
    reducer: REDUCERS,
    temp_dir: str = "",
    scale: float = 92.76624195666344,  # scale of child population data
) -> dict[str, float | dict]:
    """Reduce an image by applying a reducer to its pixels within specified regions.

    Args:
        image_filename: The path to the image to reduce
        feature_collection_filename: The path to the geometry to reduce the image to
        reducer: The reducer to apply
        scale: The scale of the image. It should be 100 unless otherwise specified.

    Returns:
        dict: A dictionary containing the reduced value

    Use case:
        Calculate the average rainfall within specific administrative boundaries:
        reduce_image("rainfall_data.json", "admin_boundaries.json", REDUCERS.MEAN)

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    logger.info(f"Reducing image with {reducer}")
    image = load_vector_data(os.path.join(temp_dir, image_filename))
    feature_collection = load_vector_data(
        os.path.join(temp_dir, feature_collection_filename)
    )
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
            "image_filename": image_filename,
            "feature_collection_filename": feature_collection_filename,
            "reducer": reducer,
            "scale": scale,
        },
    }


def build_map(
    image_filenames: list[str],
    feature_collection_filename: str,
    color_palettes: list[list[str]],
    names: list[str] = [],
    temp_dir: str = "",
) -> dict[str, str | dict]:
    """Build a map from images and vector data and save it to an HTML file.

    Creates an interactive map by overlaying Earth Engine images on top of vector data
    (e.g. administrative boundaries). The map is saved as an HTML file that can be viewed
    in a web browser.

    Each image will be a different layer in the map, with its own color palette and name.

    Args:
        image_filenames: List of paths to the Earth Engine image files to display on the map
        feature_collection_filename: Path to the vector data file (e.g. GeoJSON) defining the
            boundaries to overlay the images on
        color_palettes: List of color palettes to use for each image layer. Each palette should
            be a list of color strings (e.g. ["#ff0000", "#00ff00"])
        names: Optional list of names for each image layer. Must match length of image_filenames.
        temp_dir: Optional temporary directory for file operations. Leave empty to use default.

    Returns:
        dict: A dictionary containing the name of the saved HTML map file under the key
            'map_filename'

    Use case:
        Create an interactive map showing drought severity and population density in a region:
        build_map(["drought_data.json", "population_density.json"], "country_boundaries.json",
                 [["#ff0000", "#00ff00"], ["#0000ff", "#ffff00"]],
                ["Drought Severity", "Population Density"])

    Note:
        Do not provide a value for temp_dir, it will be handled automatically.
    """
    logger.info(
        f"Building map with {image_filenames} and {feature_collection_filename}"
    )
    vector_data = load_vector_data(os.path.join(temp_dir, feature_collection_filename))
    images = [
        load_vector_data(os.path.join(temp_dir, path)) for path in image_filenames
    ]
    if len(names) != len(image_filenames):
        raise ValueError("The number of names must be equal to the number of images")

    return {
        "map_filename": image_to_html(
            images=images,
            vector_data=vector_data,
            color_palettes=color_palettes,
            names=names,
            center=True,
            temp_dir=temp_dir,
        ),
        "input_arguments": {
            "image_filenames": image_filenames,
            "feature_collection_filename": feature_collection_filename,
            "names": names,
        },
    }


def intersect_feature(
    feature: Feature, feature_collection: FeatureCollection
) -> Feature:
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
    intersected = feature.geometry().intersection(
        feature_collection.geometry(), ErrorMargin(100)
    )
    return Feature(intersected).copyProperties(feature)
