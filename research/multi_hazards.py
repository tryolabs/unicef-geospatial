# %%
import json
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

sys.path.append(str(Path(__file__).parent.parent) + "/unicef_geospatial")
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent) + "/unicef_geospatial"

import ee
import geemap

auth_path = Path("../.secrets/ee_auth.json")
auth_file = auth_path.read_text()
auth_dict = json.loads(auth_file)
email = auth_dict["client_email"]

auth = ee.ServiceAccountCredentials(email=email, key_data=auth_file)
ee.Authenticate()
ee.Initialize(auth)

# %%

from geospatial.demographic import get_zone_of_area
from geospatial.earth_engine import get_dataset_metadata
from geospatial.io import load_vector_data
from utils.schemas import ALL_DATASETS


def calculate_multi_hazard_exposure(
    datasets: list[ALL_DATASETS], country_name="Colombia"
):
    """
    Calculate the exposure of children to multiple hazards.

    Args:
        dataset1: First dataset from ALL_DATASETS
        dataset2: Second dataset from ALL_DATASETS
        country_name: Name of the country to analyze

    Returns:
        dict: Dictionary containing exposure statistics and hazard zones
    """
    # Get metadata for both datasets
    datasets_hazard_zones = []
    for dataset in datasets:
        dataset_metadata = get_dataset_metadata(dataset)
        # Load images
        if dataset_metadata.mosaic:
            dataset_image = ee.ImageCollection(dataset_metadata.asset_id).mosaic()
        else:
            dataset_image = ee.Image(dataset_metadata.asset_id)

        dataset_zones = dataset_image.gt(dataset_metadata.threshold).unmask(0)
        datasets_hazard_zones.append(dataset_zones)

    both_hazard_zones = datasets_hazard_zones[0]
    either_hazard_zones = datasets_hazard_zones[0]
    for dataset_zones in datasets_hazard_zones[1:]:
        both_hazard_zones = both_hazard_zones.And(dataset_zones)
        either_hazard_zones = either_hazard_zones.Or(dataset_zones)

    # Get children population data
    children_population_metadata = get_dataset_metadata(
        ALL_DATASETS.CHILDREN_POPULATION
    )
    children_population_image = ee.ImageCollection(
        children_population_metadata.asset_id
    ).mosaic()

    # Mask children population with hazard zones
    children_population_hazard_both = children_population_image.mask(both_hazard_zones)
    children_population_hazard_either = children_population_image.mask(
        either_hazard_zones
    )
    children_population_hazard_datasets = []
    for dataset_zones in datasets_hazard_zones:
        children_population_hazard_dataset = children_population_image.mask(
            dataset_zones
        )
        children_population_hazard_datasets.append(children_population_hazard_dataset)

    # Get country zone
    country_zone = get_zone_of_area(country_name, "country")

    # Calculate sums
    both_hazard_sum = children_population_hazard_both.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=load_vector_data(country_zone["value"]),
        scale=100,
        maxPixels=1e13,
    ).getInfo()

    either_hazard_sum = children_population_hazard_either.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=load_vector_data(country_zone["value"]),
        scale=100,
        maxPixels=1e13,
    ).getInfo()

    dataset_hazard_sums = []
    for children_population_hazard_dataset in children_population_hazard_datasets:
        dataset_hazard_sum = children_population_hazard_dataset.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=load_vector_data(country_zone["value"]),
            scale=100,
            maxPixels=1e13,
        ).getInfo()
        dataset_hazard_sums.append(dataset_hazard_sum)

    # Create visualization map
    vis_params = {
        "min": 0,
        "max": 1,
        "palette": ["white", "black"],
    }

    map = geemap.Map()
    for dataset_zones in datasets_hazard_zones:
        map.add_layer(dataset_zones, vis_params, f"{dataset} Hazard")
    map.add_layer(both_hazard_zones, vis_params, "Both Hazards")
    map.add_layer(either_hazard_zones, vis_params, "Either Hazard")

    return {
        "both_hazard_sum": both_hazard_sum,
        "either_hazard_sum": either_hazard_sum,
        **{
            f"dataset{i+1}_hazard_sum": sum_value
            for i, sum_value in enumerate(dataset_hazard_sums)
        },
        "map": map,
        "hazard_zones": {
            **{
                f"dataset{i+1}_hazard_zones": dataset_zones
                for i, dataset_zones in enumerate(datasets_hazard_zones)
            },
            "both_hazard_zones": both_hazard_zones,
            "either_hazard_zones": either_hazard_zones,
        },
        "population_exposure": {
            "both": children_population_hazard_both,
            "either": children_population_hazard_either,
            **{
                f"dataset{i+1}": children_population_hazard_dataset
                for i, children_population_hazard_dataset in enumerate(
                    children_population_hazard_datasets
                )
            },
        },
    }


# %%
countries = ["Colombia", "Angola", "Nicaragua", "Uruguay"]
for country in countries:
    result = calculate_multi_hazard_exposure(
        [ALL_DATASETS.RIVER_FLOOD, ALL_DATASETS.COASTAL_FLOOD], country
    )
    print(f"Country: {country}")
    print(f"Both: {result['both_hazard_sum']}")
    print(f"Either: {result['either_hazard_sum']}")
    print(f"Dataset 1: {result['dataset1_hazard_sum']}")
    print(f"Dataset 2: {result['dataset2_hazard_sum']}")
    result["map"]

# %%

# %%
