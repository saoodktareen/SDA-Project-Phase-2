import pandas as pd

def process(df: pd.DataFrame, config: dict, group_by: str) -> pd.DataFrame:
    """
    Aggregates GDP based on JSON operation (sum / average)
    and groups by the specified column.
    
    Parameters:
    df        : filtered DataFrame
    config    : validated JSON config
    group_by  : column to group by (e.g., 'Continent', 'Year')
    """

    operation = config["operation"]

    grouped = df.groupby(group_by)["GDP"]

    if operation == "sum":
        result_df = grouped.sum().reset_index(name="GDP")
    elif operation == "average":
        result_df = grouped.mean().reset_index(name="GDP")
    else:
        raise ValueError("Invalid operation in config")

    return result_df
