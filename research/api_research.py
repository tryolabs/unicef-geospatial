# %%
import time
from pprint import pprint
from typing import Literal, Optional

import pandas as pd

from unicef_api import get_data, get_data_json, get_dataflow_list

# %%
all_dataflows = get_dataflow_list()
all_dataflows_ids = [dataflow["id"] for dataflow in all_dataflows]
print(all_dataflows_ids)


def get_value_from_structure(
    json_data: dict,
    structure_type: Literal["dimensions", "attributes"],
    dimension_type: Literal["observation", "series"],
    position: int,
    value_position: int,
) -> Optional[str]:
    return json_data[structure_type][dimension_type][position]["values"][
        value_position
    ]["name"]


def get_values_from_ids(
    json_data: dict,
    ids: list[int],
    structure_type: Literal["dimensions", "attributes"],
    dimension_type: Literal["observation", "series"],
):
    return [
        (
            get_value_from_structure(
                json_data,
                structure_type,
                dimension_type,
                i,
                ids[i],
            )
            if ids[i] is not None
            else None
        )
        for i in range(len(ids))
    ]


# %%
for dataflow_id in all_dataflows_ids:
    try:
        start = time.time()
        df = get_data(dataflow_id)
        print(time.time() - start)
        df.head()
    except Exception as e:
        print(f"Error for dataflow {dataflow_id}: {e}")
        continue

    def build_csv_from_json(json_data: dict):
        data_structure = json_data["structure"]

        # Get dimension and attribute definitions upfront
        dimensions = {
            "observation": [
                d["id"] for d in data_structure["dimensions"]["observation"]
            ],
            "series": [d["id"] for d in data_structure["dimensions"]["series"]],
        }
        attributes = {
            "observation": [
                a["id"] for a in data_structure["attributes"]["observation"]
            ],
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

        def get_values_fast(
            ids: list[int], structure_type: str, dimension_type: str
        ) -> list:
            lookup = value_lookups[(structure_type, dimension_type)]
            return [
                lookup.get((i, id_val)) if id_val is not None else None
                for i, id_val in enumerate(ids)
            ]

        data = json_data["dataSets"][0]["series"]
        # Process all series at once using list comprehension
        rows = [
            (
                # Observation dimensions
                get_values_fast(
                    [int(x) for x in obs_dims.split(":")], "dimensions", "observation"
                )
                + [None] * (len(dimensions["observation"]) - len(obs_dims.split(":")))
                +
                # Series dimensions
                get_values_fast(
                    [int(x) for x in series_id.split(":")], "dimensions", "series"
                )
                + [None] * (len(dimensions["series"]) - len(series_id.split(":")))
                +
                # Observation attributes
                get_values_fast(obs_attrs[1:], "attributes", "observation")
                + [None] * (len(attributes["observation"]) - len(obs_attrs[1:]))
                +
                # Series attributes
                get_values_fast(series_data["attributes"], "attributes", "series")
                + [None] * (len(attributes["series"]) - len(series_data["attributes"]))
                +
                # Observation value
                [obs_attrs[0]]
            )
            for series_id, series_data in data.items()
            if "observations" in series_data.keys()
            and "attributes" in series_data.keys()
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

    # much faster doing this!
    start = time.time()
    try:
        json = get_data_json(dataflow_id)
    except Exception as e:
        print(f"Error for dataflow {dataflow_id}: {e}")
        continue

    built_df = build_csv_from_json(json)
    print(time.time() - start)
    built_df.head()
    # check that the dataframe built is the same as the one downloaded
    is_different = False
    for col in built_df.columns:
        # Convert to string but handle NaN/None comparison and numeric equality
        built_series = built_df[col]
        df_series = df[col]

        # Try converting each value to numeric individually
        built_converted = []
        df_converted = []
        possible_nans = [
            "nan",
            "NaN",
            "NA",
            "na",
            None,
            "None",
            "NAN",
            float("nan"),
            "null",
        ]
        # Replace all possible NaN-like values with None
        built_series = built_series.apply(
            lambda x: None if pd.isna(x) or str(x) in possible_nans else x
        )
        df_series = df_series.apply(
            lambda x: None if pd.isna(x) or str(x) in possible_nans else x
        )

        for built_val, df_val in zip(built_series, df_series):
            try:
                # Try converting to numeric
                if built_val is not None:
                    built_num = pd.to_numeric(built_val)
                else:
                    built_num = None
                if df_val is not None:
                    df_num = pd.to_numeric(df_val)
                else:
                    df_num = None
                built_converted.append(built_num)
                df_converted.append(df_num)
            except:
                # Fall back to string if numeric conversion fails
                built_converted.append(
                    str(built_val) if built_val is not None else None
                )
                df_converted.append(str(df_val) if df_val is not None else None)

        # Compare values, treating None as equal to None
        is_equal = True
        for a, b in zip(built_converted, df_converted):
            if not ((pd.isna(a) and pd.isna(b)) or (a == b)):
                is_equal = False
                print(f"Found different values: {a} vs {b}")
                break

        if not is_equal:
            is_different = True
            print(f"{col} is different")
            # break

    if is_different:
        print(f"Dataframes for dataflow {dataflow_id} are different")
        # break
    else:
        print(f"Dataframes for dataflow {dataflow_id} are the same")

# %%
