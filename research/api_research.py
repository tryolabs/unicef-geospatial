# %%
import time
from pprint import pprint
from typing import Literal, Optional

import pandas as pd

from unicef_geospatial.data_warehouse.unicef_api import (
    build_csv_from_json,
    get_data,
    get_data_json,
    get_dataflow_list,
)

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
