from utils.constants import BASE_ASSETS_PATH, BASE_PATH
from utils.types import DatasetMetadata

# Earth Engine assets
DATASETS_METADATA = {
    "river_flood": DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/river_flood_r100",
        path_to_image=f"{BASE_PATH}/river_flood_image.json",
        threshold=0.01,
        greater_than=True,
        description="Zones of river flood. The value indicates the depth in meters.",
        mosaic=True,
    ),
    "coastal_flood": DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/coastal_flood_r100",
        path_to_image=f"{BASE_PATH}/coastal_flood_image.json",
        threshold=0,
        greater_than=True,
        description="Zones of coastal flood. The value is 1 if the zone is flooded, 0 otherwise.",
        mosaic=True,
    ),
    "pluvial_flood": DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/JBA_FLSW_resampled",
        path_to_image=f"{BASE_PATH}/pluvial_flood_image.json",
        threshold=0,
        greater_than=True,
        description="Zones of pluvial flood. The value indicates the depth in meters.",
        mosaic=False,
    ),
    "tropical_storm": DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/storm_giri_rp100",
        path_to_image=f"{BASE_PATH}/storm_image.json",
        threshold=17.5,
        greater_than=True,
        description="Zones affected by tropical storms.",
        mosaic=True,
    ),
    "children_population": DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/childpop_constrained",
        path_to_image=f"{BASE_PATH}/children_population_image.json",
        description="Population of children between 0-18 years old.",
        mosaic=True,
    ),
}
