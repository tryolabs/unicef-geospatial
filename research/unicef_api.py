import urllib.parse

import pandas as pd
import requests

BASE_URL = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/"


def get_dataflow_list():
    url = urllib.parse.urljoin(
        BASE_URL,
        "dataflow/all/all/latest/?format=sdmx-json&detail=full&references=none",
    )
    response = requests.get(url)
    return response.json()["data"]["dataflows"]


def get_data(dataflow_id: str):
    url = urllib.parse.urljoin(BASE_URL, f"data/{dataflow_id}/All?format=csv")
    data = pd.read_csv(url)
    return data


def get_data_json(dataflow_id: str):
    url = urllib.parse.urljoin(BASE_URL, f"data/{dataflow_id}/All?format=sdmx-json")
    data = requests.get(url).json()
    if "errors" in data.keys():
        raise Exception(data["errors"])
    return data["data"]


def build_csv_from_json(json_data: dict):
    print(json_data.keys())
    dimensions = json_data["structure"]["dimensions"]
    print(dimensions)
    return


def convert_columns_to_snake_case(df: pd.DataFrame) -> pd.DataFrame:
    """Convert DataFrame column names to snake case and handle duplicates.

    Converts all column names to lowercase and adds numeric suffixes to handle duplicate names.
    For example, columns ["Name", "NAME"] would become ["name", "name_1"].

    Args:
        df: The input DataFrame whose columns should be converted

    Returns:
        DataFrame with converted column names
    """
    seen = {}
    new_columns = []
    for col in df.columns:
        col_lower = col.lower()
        if col_lower not in seen:
            seen[col_lower] = 1
        else:
            seen[col_lower] += 1
            col_lower = f"{col_lower}_{seen[col_lower] - 1}"
        new_columns.append(col_lower)
    df.columns = new_columns
    return df


def drop_even_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop even columns from the DataFrame.

    Args:
        df: The input DataFrame

    Returns:
        DataFrame with even columns dropped
    """
    even_columns = []
    print(df.columns)
    for i, col in enumerate(df.columns, start=1):
        if i % 2 == 0:
            even_columns.append(col)
    return df.drop(columns=even_columns)


def preprocess_data(df: pd.DataFrame):
    # remove spaces
    df = drop_even_columns(df)
    df.columns = df.columns.str.replace(" ", "_")
    df = convert_columns_to_snake_case(df)
    return df
