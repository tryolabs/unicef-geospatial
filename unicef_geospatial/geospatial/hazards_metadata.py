from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.retrievers import VectorIndexRetriever
from utils.constants import (
    BASE_ASSETS_PATH,
    CCRI_METADATA_PERSIST_DIR,
)
from utils.types import ALL_DATASETS, DatasetMetadata

vector_index = load_index_from_storage(
    StorageContext.from_defaults(persist_dir=CCRI_METADATA_PERSIST_DIR)
)


def get_ccri_metadata(query: str, temp_dir: str = "") -> str:
    """Get the metadata for the CCRI dataset.

    The documentation contains detailed information about the CCRI methodology,
    data sources, and technical specifications for the Climate Change Risk Index.

    This function uses a vector index to search the CCRI technical documentation.
    It returns the most relevant information from the documentation based on the query.

    Args:
        query: The query to search the CCRI technical documentation.
        temp_dir: Temporary directory path. This parameter is not used but is required
                 for compatibility with the tool framework.

    Returns:
        The most relevant chunks from the CCRI technical documentation as a string.
    """
    retriever = VectorIndexRetriever(
        index=vector_index,
        similarity_top_k=5,
    )

    response = retriever.retrieve(query)
    return "\n".join([r.text for r in response])


# Earth Engine assets
DATASETS_METADATA = {
    ALL_DATASETS.CHILDREN_POPULATION: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/childpop_constrained",
        image_filename="children_population_image.json",
        description="Population of children between 0-18 years old.",
        mosaic=True,
        source_name="WorldPop",
        source_url="https://www.worldpop.org/",
    ),
    ALL_DATASETS.RIVER_FLOOD: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/river_flood_r100",
        image_filename="river_flood_image.json",
        threshold=0.01,
        description="Zones of river flood. The value indicates the depth in meters.",
        mosaic=True,
        source_name="Joint Research Center",
        source_url="https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/",
    ),
    ALL_DATASETS.COASTAL_FLOOD: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/coastal_flood_r100",
        image_filename="coastal_flood_image.json",
        threshold=0,
        description="Zones of coastal flood. The value is 1 if the zone is flooded, 0 otherwise.",
        mosaic=True,
        source_name="Joint Research Center",
        source_url="https://data.jrc.ec.europa.eu/dataset/9e5ba6f1-8d03-4834-8488-2353e504560f",
    ),
    ALL_DATASETS.TROPICAL_STORM: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/storm_giri_rp100",
        image_filename="storm_image.json",
        threshold=17.5,
        description="Zones affected by tropical storms.",
        mosaic=True,
        source_name="STORM",
        source_url="https://data.4tu.nl/datasets/0ea98bdd-5772-4da8-ae97-99735e891aff/4",
    ),
    ALL_DATASETS.AGRICULTURAL_DROUGHT: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/ASI_return_level_100yr",
        image_filename="agricultural_drought_image.json",
        description="Agricultural drought return level for 100 years.",
        mosaic=False,
        threshold=30,
        source_name="Food and Agriculture Organization of the United Nations",
        source_url="https://www.fao.org/giews/earthobservation/asis/index_1.jsp?lang=en",
    ),
    ALL_DATASETS.DROUGHT_SPEI: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/spei12_period_mean_2014_2024",
        image_filename="drought_spei_image.json",
        description="Standardized Precipitation-Evapotranspiration Index (SPEI) drought indicator.",
        mosaic=False,
        threshold=-1,
        source_name="Copernicus",
        source_url="https://cds.climate.copernicus.eu/",
    ),
    ALL_DATASETS.DROUGHT_SPI: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/spi12_period_mean_2014_2024",
        image_filename="drought_spi_image.json",
        description="Standardized Precipitation Index (SPI) drought indicator.",
        mosaic=False,
        threshold=-1,
        source_name="Copernicus",
        source_url="https://cds.climate.copernicus.eu/",
    ),
    ALL_DATASETS.HEATWAVE_FREQUENCY: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/heatwave_frequency_return_level_100yr",
        image_filename="heatwave_frequency_image.json",
        description="Frequency of heatwaves, 100-year return level.",
        mosaic=False,
        threshold=16.8,
        source_name="ECMWF",
        source_url="https://www.ecmwf.int/",
    ),
    ALL_DATASETS.HEATWAVE_DURATION: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/heatwave_duration_return_level_100yr",
        image_filename="heatwave_duration_image.json",
        description="Duration of heatwaves, 100-year return level.",
        mosaic=False,
        threshold=89.8,
        source_name="ECMWF",
        source_url="https://www.ecmwf.int/",
    ),
    ALL_DATASETS.HEATWAVE_SEVERITY: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/heatwave_severity_return_level_100yr",
        image_filename="heatwave_severity_image.json",
        description="Severity of heatwaves, 100-year return level.",
        mosaic=False,
        threshold=3.8,
        source_name="ECMWF",
        source_url="https://www.ecmwf.int/",
    ),
    ALL_DATASETS.EXTREME_HEAT: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/high_temp_degree_days_return_level_100yr",
        image_filename="extreme_heat_image.json",
        description="Extreme heat degree days, 100-year return level.",
        mosaic=False,
        threshold=35,
        source_name="ECMWF",
        source_url="https://www.ecmwf.int/",
    ),
    ALL_DATASETS.FIRE_FRP: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/FIRMS_FRP_90th_percentile",
        image_filename="fire_frp_image.json",
        description="Fire Radiative Power (FRP) 90th percentile.",
        mosaic=False,
        threshold=37.8,
        source_name="NASA",
        source_url="https://firms.modaps.eosdis.nasa.gov/",
    ),
    ALL_DATASETS.FIRE: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/FIRMS_count_90th_percentile",
        image_filename="fire_image.json",
        description="Fire frequency 90th percentile.",
        mosaic=False,
        threshold=4.9,
        source_name="NASA",
        source_url="https://firms.modaps.eosdis.nasa.gov/",
    ),
    ALL_DATASETS.SAND_DUST_STORM: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/sand_dust_storm_annual",
        image_filename="sand_dust_storm_image.json",
        description="Number of sand dust storms in the last 24 years.",
        mosaic=False,
        threshold=0,
        source_name="UNCCD",
        source_url="https://www.unccd.int/data-knowledge",
    ),
    ALL_DATASETS.AIR_POLLUTION: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/pm25_p90_1998_2023",
        image_filename="air_pollution_image.json",
        description="PM2.5 90th percentile concentration from 1998 to 2023. This is a proxy for air pollution.",
        mosaic=False,
        threshold=5,
        source_name="ACAG",
        source_url="https://sites.wustl.edu/acag/datasets/surface-pm2-5/",
    ),
    ALL_DATASETS.PLASMODIUM_VIVAX: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/Pv_average_2013_2022",
        image_filename="plasmodium_vivax_image.json",
        description="Incidente rate of malaria due to Plasmodium vivax.",
        mosaic=False,
        threshold=0.001,
        source_name="Malaria Atlas Project",
        source_url="https://apps.who.int/malaria/maps/threats/#/download",
    ),
    ALL_DATASETS.PLASMODIUM_FALCIPARUM: DatasetMetadata(
        asset_id=f"{BASE_ASSETS_PATH}/Pf_average_2013_2022",
        image_filename="plasmodium_falciparum_image.json",
        description="Incidente rate of malaria due to Plasmodium falciparum.",
        mosaic=False,
        threshold=0.001,
        source_name="Malaria Atlas Project",
        source_url="https://apps.who.int/malaria/maps/threats/#/download",
    ),
}
