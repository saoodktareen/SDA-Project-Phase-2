import pandas as pd
from typing import Dict, Any

def process(df: pd.DataFrame, config: Dict[str, Any], group_by: str) -> pd.DataFrame:
    """
    Aggregates GDP based on the operation specified in config.
    Used both for region-level and country-level summaries.
    
    Phase 1 requirement: supports 'sum' and 'average'
    Phase 2: pure function, no side effects, called from engine.
    """
    operation = config.get("operation")

    if operation not in {"sum", "average"}:
        raise ValueError(f"Invalid operation: {operation}. Must be 'sum' or 'average'")

    if df.empty:
        return pd.DataFrame(columns=[group_by, "GDP"])

    grouped = df.groupby(group_by)["GDP"]

    if operation == "sum":
        result = grouped.sum().reset_index(name="GDP")
    else:  # average
        result = grouped.mean().reset_index(name="GDP")

    # Optional: round for nicer display (Phase 1 style)
    result["GDP"] = result["GDP"].round(2)

    return result