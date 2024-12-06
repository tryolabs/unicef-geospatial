# %%
import time

import pandas as pd
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from pandasai import Agent
from pandasai.skills import skill

from unicef_api import get_data, preprocess_data

load_dotenv(override=True)

# dataflow_id = "CHLD_PVTY"
# start = time.time()
# df = get_data(dataflow_id)
# print(f"Time taken to get data: {time.time() - start} seconds")
# start = time.time()
# df = preprocess_data(df)
# print(f"Time taken to preprocess data: {time.time() - start} seconds")
# df.head()

# %%
pd.set_option("display.max_columns", None)
dataflow_id = "DM"
start = time.time()
df = get_data(dataflow_id)
print(f"Time taken to get data: {time.time() - start} seconds")
start = time.time()
df = preprocess_data(df)
print(f"Time taken to preprocess data: {time.time() - start} seconds")
df.head()

# %%
df.columns


# %%
def get_dataframe_columns() -> dict[str, str]:
    """Get the columns of the dataframe with it's type
    Returns:
        dict[str, str]: The columns of the dataframe with their type
    """
    return {col: df[col].dtype for col in df.columns}


# %%
def keep_columns(
    df: pd.DataFrame,
    columns: list[str] = ["Country", "Indicator", "Sex", "TIME_PERIOD", "OBS_VALUE"],
) -> pd.DataFrame:
    """Keep only the relevant columns of the dataframe
    Args:
        df (pd.DataFrame): The dataframe to filter
    Returns:
        pd.DataFrame: The filtered dataframe
    """
    return df[columns]


df = keep_columns(df)
# %%
SYSTEM_PROMPT = str(
    """
You are working with a pandas dataframe in Python. The name of the dataframe is `df`.

Your answer should produce valid python code, without any syntax errors \
and should be executable by python_repl_ast. \
If you get an error, use a different approach to get the answer. \
Do a step by step reasoning to get the answer. \
Analyze the question and the dataframe to understand which columns are relevant. \
Use the skills you have to get the answer. \
If the question doesn't have any year, use the latest year available. \
I am now going to give you some information about the dataframe. \
Here are the first 5 rows of the dataframe:
{df_head}
Here are the columns of the dataframe with their type:
{df_columns}
Here is a description of the most relevant columns:
    - country or geographic_area: The country of the observation
    - indicator: The measurement or metric being recorded. Examples include:
        - "Percentage of population under poverty line"
        - "Number of children under 18"
        - "Percentage children suffering deprivation"
        - "Poverty Level"
    - sex: The sex of the observation
    - time_period: The year of the observation
    - obs_value: The value of the observation
""".replace(
        "{df_head}", df.head().to_string()
    ).replace(
        "{df_columns}", str(get_dataframe_columns())
    )
)


def create_skills(df: pd.DataFrame):
    @skill
    def get_dataframe_for_ref_area(ref_area: str) -> pd.DataFrame:
        """Filter the dataframe for a given country
        Args:
            ref_area (str): The country to filter the dataframe for
        Returns:
            pd.DataFrame: The filtered dataframe
        """
        return df[df["ref_area"] == ref_area]

    return [get_dataframe_for_ref_area]


# %%
questions = [
    # "What's the poverty level in Argentina?",
    "how many children under 18 are there in colombia in 2023?",
]
llm = ChatCohere()
agent = Agent(df, config={"llm": llm, "verbose": True}, description=SYSTEM_PROMPT)
agent.add_skills(*create_skills(df))
results = []
for question in questions:
    result = agent.chat(question)
    results.append(result)

# %%
results


# %%
pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)
colombia_df = df[df["REF_AREA"] == "COL"]
children_under_18 = colombia_df[colombia_df["INDICATOR"] == "DM_POP_U18"]
children_under_18
# %%
num_children_under_18 = children_under_18["OBS_VALUE"].sum()
result = {"type": "number", "value": num_children_under_18}
result
# %%
