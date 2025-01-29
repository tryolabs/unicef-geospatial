# %%
# objective: answer the question: How many children are exposed to heatwaves globally in 2024?
# %%

import ee
import geemap

ee.Initialize()

DROUGHT_DATASET = "CSIC/SPEI/2_10"
SPEI_BAND = "SPEI_01_month"
DEMOGRAPHIC_DATASET = "CIESIN/GPWv411/GPW_Population_Count"
DEMOGRAPHIC_BAND = "population_count"
# %%


def get_drought_zones(
    drought_threshold: float,
    year: int = 2000,
    month: int = 1,
    day: int = 1,
    max_vertices: int = 1000,
) -> ee.FeatureCollection:
    """Get drought zones and their vector representations for a given date and threshold.

    Args:
        drought_threshold: SPEI value threshold below which is considered drought
        year: Year to analyze
        month: Month to analyze (1-12)
        day: Day to analyze (1-31)
        max_vertices: Maximum number of vertices for polygon simplification

    Returns:
        Tuple containing:
        - ee.Image: Binary mask of drought areas
        - ee.FeatureCollection: Vector polygons of drought areas with properties
        - ee.Image: Original drought image
    """
    # Get the drought image for the specified date
    drought_dataset = ee.ImageCollection(DROUGHT_DATASET)
    drought_image = (
        drought_dataset.filter(
            ee.Filter.eq("system:index", f"{year}_{month:02d}_{day:02d}")
        )
        .select(SPEI_BAND)
        .first()
    )

    scale = drought_image.select(SPEI_BAND).projection().nominalScale().getInfo()

    # Create mask where values are below threshold
    drought_mask = drought_image.unmask(-999).lt(drought_threshold)

    # Apply the mask to the original image
    masked_drought = drought_image.updateMask(drought_mask).toInt()

    try:

        earth_geometry = ee.Geometry.Polygon(
            [-180, 85, 0, 85, 180, 85, 180, -85, 0, -85, -180, -85],
            "EPSG:4326",
            False,
        )

        vectors = masked_drought.reduceToVectors(
            geometry=earth_geometry,
            scale=scale,
            geometryType="polygon",
            eightConnected=True,
            labelProperty="drought_value",
            maxPixels=1e13,
            crs="EPSG:4326",
        )

        # Simplify geometries while preserving topology
        simplified_vectors = vectors.map(
            lambda f: f.simplify(max_vertices).set(
                {
                    "year": year,
                    "month": month,
                    "day": day,
                    "threshold": drought_threshold,
                    "date": f"{year}-{month:02d}-{day:02d}",
                    "area_km2": f.geometry()
                    .area(1000)
                    .divide(1000),  # Add area in km² with error margin
                }
            )
        )

        # Filter out any invalid or tiny polygons
        final_vectors = simplified_vectors.filter(
            ee.Filter.And(
                ee.Filter.neq("drought_value", None),
                ee.Filter.gt(
                    "area_km2", 100
                ),  # Increased minimum area threshold for global analysis
            )
        )

    except Exception as e:
        print(f"Error in vector conversion: {str(e)}")
        return ee.FeatureCollection([])

    return final_vectors


drought_vectors = get_drought_zones(-2)

Map = geemap.Map()
Map.add_layer(drought_vectors, {"min": 0, "max": 1}, "Drought vectors")
Map


# %%


def get_population_in_drought_zones(
    drought_threshold: float,
    age_group: str = "0-14",
    sex: str = "b",
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

    drought_vectors = get_drought_zones(drought_threshold)

    demographic = ee.ImageCollection(DEMOGRAPHIC_DATASET).first()
    scale = demographic.select(DEMOGRAPHIC_BAND).projection().nominalScale().getInfo()

    masked_demographic = demographic.clip(drought_vectors)
    result = masked_demographic.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=drought_vectors,
        scale=scale,
        maxPixels=1e14,
    ).getInfo()

    population_count = result.get(DEMOGRAPHIC_BAND, 0)

    return population_count, masked_demographic, drought_vectors


# esto da valores muy bajos, tiene pinta de ser el mismo problema que el de abajo
drought_threshold = 1
import time

print("\nDrought Analysis Results")
print("-" * 80)
print(f"{'SPEI Threshold':<15} {'Population':<15} {'Time (s)':<10}")
print("-" * 80)

for drought_threshold in [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]:
    start_time = time.time()
    population_in_drought, masked_demographic, drought_vectors = (
        get_population_in_drought_zones(drought_threshold)
    )
    execution_time = time.time() - start_time

    print(
        f"{drought_threshold:<15} "
        f"{f'{population_in_drought:,.0f}':<15} "
        f"{execution_time:.2f}"
    )

# %%
