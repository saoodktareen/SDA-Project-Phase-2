import pandas as pd
from typing import Dict, Union, List

def filter_by_region(df: pd.DataFrame, config: Dict[str, Union[str, List[str], int]]) -> pd.DataFrame:
    """
    Filters DataFrame by region(s) / continent(s) specified in config.
    Phase 1: Supports single or multiple regions.
    Phase 2: Pure function, no side effects.
    Functional style: uses .isin() and boolean indexing.
    """
    # Get region key (your config uses "continent", but Phase 1 doc says "region" — make compatible)
    region_key = "Continent"  # Column name in data
    regions = config.get("region", []) or config.get("continent", [])
    
    # Normalize to list
    if isinstance(regions, str):
        regions = [regions]
    elif not isinstance(regions, list):
        regions = []

    if not regions:
        # No region filter → return original
        return df.copy()

    # Filter rows where Continent is in the list
    mask = df[region_key].isin(regions)
    
    filtered = df[mask].copy()
    
    # Year filter (restored from Phase 1)
    if "year" in config:
        years = config["year"]
        years = [years] if isinstance(years, int) else years if isinstance(years, list) else []
        if years:
            filtered = filtered[filtered["Year"].isin(years)]
    
    print(f"[DEBUG FILTER REGION] Filtered by {regions}: {len(filtered)} rows remain")
    
    return filtered