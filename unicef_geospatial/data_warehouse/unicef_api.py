import urllib.parse
from typing import Any, Literal

import pandas as pd
import requests

BASE_URL = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/"
OUTPUT_FORMATS = Literal["sdmx-json", "csv"]


def get_dataflow_list() -> list[dict[str, Any]]:
    """Get list of available dataflows from UNICEF API.

    Returns:
        List[Dict[str, Any]]: List of dataflow dictionaries containing metadata
    """
    url = urllib.parse.urljoin(
        BASE_URL,
        "dataflow/all/all/latest/?format=sdmx-json&detail=full&references=none",
    )
    response = requests.get(url, timeout=200)
    return response.json()["data"]["dataflows"]


def get_data(
    dataflow_id: str,
    ref_areas: list[str] | None = None,
    indicators: list[str] | None = None,
    output_format: OUTPUT_FORMATS = "sdmx-json",
) -> pd.DataFrame:
    """Get data for a specific dataflow ID in JSON format.

    Args:
        dataflow_id (str): ID of the dataflow to retrieve
        ref_areas (list[str]): List of reference areas to retrieve
        indicators (list[str]): List of indicators to retrieve
        output_format (OUTPUT_FORMATS): Format of the output data

    Returns:
        Dict[str, Any]: Dictionary containing the requested data

    Raises:
        Exception: If the API returns an error response
    """
    if indicators is not None or ref_areas is not None:
        indicators = indicators or []
        ref_areas = ref_areas or []
        indicators_str = "+".join(indicators)
        ref_areas_str = "+".join(ref_areas)
        url = urllib.parse.urljoin(
            BASE_URL,
            f"data/{dataflow_id}/{ref_areas_str}.{indicators_str}?format={output_format}",
        )
    else:
        url = urllib.parse.urljoin(
            BASE_URL, f"data/{dataflow_id}/All?format={output_format}"
        )

    if output_format == "csv":
        return pd.read_csv(url)

    data = requests.get(url, timeout=200).json()
    if "errors" in data:
        raise Exception(data["errors"])
    return build_df_from_json(data["data"])


def get_values(
    ids: list[int],
    structure_type: str,
    dimension_type: str,
    value_lookups: dict[tuple[str, str], dict[tuple[int, int], int]],
) -> list:
    lookup = value_lookups[(structure_type, dimension_type)]
    return [lookup.get((i, id_val)) for i, id_val in enumerate(ids)]


def build_df_from_json(json_data: dict) -> pd.DataFrame:
    """Build a CSV DataFrame from SDMX-JSON data.

    Args:
        json_data (dict): JSON data from API response

    Returns:
        pd.DataFrame: DataFrame containing the requested data
    """
    data_structure = json_data["structure"]

    # Get dimension and attribute definitions upfront
    dimensions = {
        "observation": [d["id"] for d in data_structure["dimensions"]["observation"]],
        "series": [d["id"] for d in data_structure["dimensions"]["series"]],
    }
    attributes = {
        "observation": [a["id"] for a in data_structure["attributes"]["observation"]],
        "series": [a["id"] for a in data_structure["attributes"]["series"]],
    }

    # Create lookup dictionaries for faster value retrieval
    value_lookups = {
        ("dimensions", "observation"): {
            (i, val_pos): val["id"]
            for i, dim in enumerate(data_structure["dimensions"]["observation"])
            for val_pos, val in enumerate(dim["values"])
        },
        ("dimensions", "series"): {
            (i, val_pos): val["id"]
            for i, dim in enumerate(data_structure["dimensions"]["series"])
            for val_pos, val in enumerate(dim["values"])
        },
        ("attributes", "observation"): {
            (i, val_pos): val["id"]
            for i, attr in enumerate(data_structure["attributes"]["observation"])
            for val_pos, val in enumerate(attr["values"])
        },
        ("attributes", "series"): {
            (i, val_pos): val["id"]
            for i, attr in enumerate(data_structure["attributes"]["series"])
            for val_pos, val in enumerate(attr["values"])
        },
    }

    data = json_data["dataSets"][0]["series"]
    # Process all series at once using list comprehension
    rows = [
        (
            # Observation dimensions
            get_values(
                [int(x) for x in obs_dims.split(":")],
                "dimensions",
                "observation",
                value_lookups,
            )
            + [None] * (len(dimensions["observation"]) - len(obs_dims.split(":")))
            +
            # Series dimensions
            get_values(
                [int(x) for x in series_id.split(":")],
                "dimensions",
                "series",
                value_lookups,
            )
            + [None] * (len(dimensions["series"]) - len(series_id.split(":")))
            +
            # Observation attributes
            get_values(obs_attrs[1:], "attributes", "observation", value_lookups)
            +
            # Series attributes
            get_values(series_data["attributes"], "attributes", "series", value_lookups)
            + [None] * (len(attributes["series"]) - len(series_data["attributes"]))
            +
            # Observation value
            [obs_attrs[0]]
        )
        for series_id, series_data in data.items()
        if "observations" in series_data and "attributes" in series_data
        for obs_dims, obs_attrs in series_data["observations"].items()
    ]

    column_names = (
        dimensions["observation"]
        + dimensions["series"]
        + attributes["observation"]
        + attributes["series"]
        + ["OBS_VALUE"]
    )

    return pd.DataFrame(rows, columns=column_names)
