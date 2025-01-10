# %%
# objective: answer the question: How many children are exposed to heatwaves globally in 2024?
# %%

import ee
import geemap

ee.Initialize()

DROUGHT_DATASET = "CSIC/SPEI/2_9"
SPEI_BAND = "SPEI_01_month"
DEMOGRAPHIC_DATASET = "CIESIN/GPWv411/GPW_Population_Count"
DEMOGRAPHIC_BAND = "population_count"


def get_drought_zones(
    drought_threshold: float, year: int = 2000, month: int = 1, day: int = 1
) -> tuple[ee.Image, ee.FeatureCollection]:
    """Get drought zones and their vector representations for a given date and threshold.

    Args:
        drought_threshold: SPEI value threshold below which is considered drought
        year: Year to analyze
        month: Month to analyze (1-12)
        day: Day to analyze (1-31)

    Returns:
        Tuple containing:
        - ee.Image: Binary mask of drought areas
        - ee.FeatureCollection: Vector polygons of drought areas with properties
    """
    drought_dataset = ee.ImageCollection(DROUGHT_DATASET)
    drought_image = drought_dataset.filter(
        ee.Filter.eq("system:index", f"{year}_{month:02d}_{day:02d}")
    ).first()

    drought_zones = drought_image.select(SPEI_BAND).unmask().lt(drought_threshold)

    vectors = drought_zones.selfMask().reduceToVectors(
        geometry=ee.Geometry.Rectangle([[-179.9, -89.9], [179.9, 89.9]]),
        scale=1000,
        geometryType="polygon",
        eightConnected=True,
        maxPixels=1e14,
        geometryInNativeProjection=True,
    )

    vectors_with_props = vectors.map(
        lambda f: f.set(
            {
                "drought_threshold": drought_threshold,
                "date": f"{year}-{month:02d}-{day:02d}",
                "area_km2": f.geometry().area().divide(1e6),
            }
        )
    )

    return drought_zones, vectors_with_props


def get_population_in_drought_zones(
    drought_threshold: float, age_group: str = "0-14", sex: str = "b"
) -> tuple[float, ee.Image, ee.Image, ee.FeatureCollection]:
    """Calculate population in areas with drought below the given threshold.

    Args:
        drought_threshold: SPEI value threshold below which is considered drought
        age_group: Age group to analyze (not currently used)
        sex: Sex to analyze (not currently used)

    Returns:
        Tuple containing:
        - float: Total population count in drought zones
        - ee.Image: Masked demographic image showing population in drought zones
        - ee.Image: Binary mask of drought zones
        - ee.FeatureCollection: Vector polygons of drought zones
    """
    drought_zones, drought_vectors = get_drought_zones(drought_threshold)

    demographic = ee.ImageCollection(DEMOGRAPHIC_DATASET).first()
    scale = demographic.select(DEMOGRAPHIC_BAND).projection().nominalScale().getInfo()
    print(drought_zones.getInfo())
    masked_demographic = demographic.clip(drought_vectors)
    result = masked_demographic.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=drought_vectors,
        scale=scale,
        maxPixels=1e14,
    ).getInfo()

    population_count = result.get(DEMOGRAPHIC_BAND, 0)

    return population_count, masked_demographic, drought_zones, drought_vectors


# esto da valores muy bajos, tiene pinta de ser el mismo problema que el de abajo
drought_threshold = -0.9
population_in_drought, masked_demographic, drought_zones, drought_vectors = (
    get_population_in_drought_zones(drought_threshold)
)
print(
    f"Population in drought zones (SPEI < {drought_threshold}):", population_in_drought
)

Map = geemap.Map()
vis = {"min": 0, "max": 1}
Map.add_layer(drought_zones, vis, "Drought zones")
Map.add_layer(masked_demographic, vis, "Population in drought zones")
Map.add_layer(
    masked_demographic.select(DEMOGRAPHIC_BAND),
    {"min": 0, "max": 1},
    "Population in drought zones",
)
Map

# %%
# get total population in the world
# esto da mal
global_geometry = ee.Geometry.Rectangle([[-179.9, -89.9], [179.9, 89.9]]).transform(
    "EPSG:4326"
)
demographic = ee.ImageCollection(DEMOGRAPHIC_DATASET).first()
demographic_global = demographic.select(DEMOGRAPHIC_BAND)
scale = demographic_global.projection().nominalScale().getInfo()
total_population = demographic_global.reduceRegion(
    reducer=ee.Reducer.sum(), geometry=global_geometry, scale=scale, maxPixels=1e14
).getInfo()

print(total_population)
Map = geemap.Map()
vis = {
    "max": 1000.0,
    "palette": ["ffffe7", "86a192", "509791", "307296", "2c4484", "000066"],
    "min": 0.0,
}
Map.add_layer(demographic_global, vis, "Demographic global")
Map.add_layer(global_geometry, {}, "Global geometry")
Map

# %%
# get total population in Uruguay
# esto anda
country_boundries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
country_boundries_uruguay = country_boundries.filter(
    ee.Filter.eq("country_na", "Uruguay")
)

demographic_uruguay = demographic.clip(country_boundries_uruguay)

total_population_uruguay = demographic_uruguay.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=country_boundries_uruguay,
    scale=scale,
    maxPixels=1e14,
).getInfo()

print(total_population_uruguay)

# %%
# siento que algo por este lado puede andar bien pero no corre en la vida
# https://code.earthengine.google.com/76f608f35460bd6287173cef2f9e940c
# en ese link sigue un approach similar pero no corre
total_population = demographic_global.reduceRegions(
    reducer=ee.Reducer.sum(), scale=scale, collection=country_boundries
).getInfo()

print(total_population)

# %%
