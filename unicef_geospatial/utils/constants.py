# Datasets
# COUNTRY_BOUNDRIES_DATASET = "USDOS/LSIB_SIMPLE/2017"
BASE_ASSETS_PATH = "projects/unicef-ccri/assets"
COUNTRY_BOUNDRIES_DATASET = f"{BASE_ASSETS_PATH}/adm0_wfp"
ADMIN_LEVEL_1_BOUNDRIES_DATASET = "WM/geoLab/geoBoundaries/600/ADM1"
HEATWAVE_DATASET = f"{BASE_ASSETS_PATH}/heatwave/average_hwi"


# Earth geometry
EARTH_GEOMETRY_COORDS = [-180, 85, 0, 85, 180, 85, 180, -85, 0, -85, -180, -85]
EARTH_GEOMETRY_CRS = "EPSG:4326"


# Paths
BASE_PATH = "unicef_geospatial/data"
MAP_FILENAME = "map_data.html"
HEATWAVE_FILENAME = "heatwave_image.json"
FEATURE_COLLECTION_FILENAME = "map_zones_feature_collection.json"
INTERSECTION_FILENAME = "intersection.json"
UNION_FILENAME = "union.json"

# CCRI
CCRI_METADATA_FILENAME = "unicef_geospatial/data/CCRI_2025_Technical_Documentation.md"
CCRI_METADATA_PERSIST_DIR = "unicef_geospatial/data/vector_index"
