from utils.constants import BASE_ASSETS_PATH, BASE_PATH
from utils.types import ALL_DATASETS, DatasetMetadata

# Earth Engine assets
DATASETS_METADATA = {
    ALL_DATASETS.RIVER_FLOOD: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/river_flood_r100",
        path_to_image=f"{BASE_PATH}/river_flood_image.json",
        threshold=0.01,
        greater_than=True,
        description="Zones of river flood. The value indicates the depth in meters.",
        mosaic=True,
    ),
    ALL_DATASETS.COASTAL_FLOOD: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/coastal_flood_r100",
        path_to_image=f"{BASE_PATH}/coastal_flood_image.json",
        threshold=0,
        greater_than=True,
        description="Zones of coastal flood. The value is 1 if the zone is flooded, 0 otherwise.",
        mosaic=True,
    ),
    ALL_DATASETS.PLUVIAL_FLOOD: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/JBA_FLSW_resampled",
        path_to_image=f"{BASE_PATH}/pluvial_flood_image.json",
        threshold=0,
        greater_than=True,
        description="Zones of pluvial flood. The value indicates the depth in meters.",
        mosaic=False,
    ),
    ALL_DATASETS.TROPICAL_STORM: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/storm_giri_rp100",
        path_to_image=f"{BASE_PATH}/storm_image.json",
        threshold=17.5,
        greater_than=True,
        description="Zones affected by tropical storms.",
        mosaic=True,
    ),
    ALL_DATASETS.CHILDREN_POPULATION: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/childpop_constrained",
        path_to_image=f"{BASE_PATH}/children_population_image.json",
        description="Population of children between 0-18 years old.",
        mosaic=True,
    ),
    ALL_DATASETS.AGRICULTURAL_DROUGHT: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/ASI_cropland_avg_2014_2023",
        path_to_image=f"{BASE_PATH}/agricultural_drought_image.json",
        description="Average annual temperature of cropland in the last 10 years.\
        Note: The image must be masked where the values is less than 100.",
        mosaic=False,
        threshold=50,
        greater_than=True,
    ),
    ALL_DATASETS.FIRE: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/FIRMS_MODIS_Mean_Annual_Count_2001_2023",
        path_to_image=f"{BASE_PATH}/fire_image.json",
        description="Number of fire events in the last 24 years.",
        mosaic=False,
        threshold=10,
        greater_than=True,
    ),
    ALL_DATASETS.SAND_DUST_STORM: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/sand_dust_storm_annual",
        path_to_image=f"{BASE_PATH}/sand_dust_storm_image.json",
        description="Number of sand dust storms in the last 24 years.",
        mosaic=False,
        threshold=0,
        greater_than=True,
    ),
}
