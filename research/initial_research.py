# %%
from pprint import pprint

import pandas as pd
from dotenv import load_dotenv
from langchain.agents import AgentType
from langchain.callbacks import get_openai_callback
from langchain.tools import tool
from langchain_cohere.llms import Cohere
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from unicef_api import get_data, get_dataflow_list

load_dotenv(override=True)

# dataflows = get_dataflow_list()
dataflow_id = "CHLD_PVTY"
df = get_data(dataflow_id)


# %%
def create_tools(df: pd.DataFrame):
    @tool("Get the first 5 rows of the dataframe")
    def get_dataframe():
        """Returns the first 5 rows of the dataframe"""
        return df.head()

    @tool("Get the column names of the dataframe")
    def get_dataframe_columns():
        """Returns a list of all column names in the dataframe"""
        return df.columns

    @tool("Gets info about the dataframe")
    def get_dataframe_info():
        """Returns a string with info about the dataframe"""
        return df.info()

    return [get_dataframe, get_dataframe_columns, get_dataframe_info]


# %%
llm = Cohere(temperature=0.0)

TEMPLATE = """
You are working with a pandas dataframe in Python. The name of the dataframe is `df`.

Your answer should produce valid python code, without any syntax errors \
and should be executable by python_repl_ast.
If you get an error, use a different approach to get the answer.
Do a step by step reasoning to get the answer.
Analyze the question and the dataframe to understand which columns are relevant.
Here are the first 5 rows of the dataframe:
{df_head}
""".replace(
    "{df_head}", df.head().to_string()
)

agent = create_pandas_dataframe_agent(
    llm,
    df,
    verbose=True,
    include_df_in_prompt=True,
    prefix=TEMPLATE,
    allow_dangerous_code=True,
    handle_parse_errors=True,
    max_iterations=5,
    extra_tools=create_tools(df),
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

with get_openai_callback() as cb:
    result = agent.invoke("Whats the poverty level between adolescents in Argentina?")
    print(result)
    print(f"\nTotal Tokens: {cb.total_tokens}")
    print(f"Prompt Tokens: {cb.prompt_tokens}")
    print(f"Completion Tokens: {cb.completion_tokens}")
    print(f"Total Cost (USD): ${cb.total_cost}")

# %%
