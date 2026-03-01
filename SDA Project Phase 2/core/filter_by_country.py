import pandas as pd
from typing import Dict, Union, List

def filter_by_country(df: pd.DataFrame, config: Dict[str, Union[str, List[str], int]]) -> pd.DataFrame:
    """
    Filters DataFrame by country(s) specified in config.
    Phase 1 special rule: If single region is given and no countries, 
    automatically include all countries in that region (handled in engine.py).
    Phase 2: Pure function, functional style.
    """
    countries = config.get("country", [])
    
    # Normalize to list
    if isinstance(countries, str):
        countries = [countries]
    elif not isinstance(countries, list):
        countries = []

    if not countries:
        # No country filter → return original
        return df.copy()

    # Filter rows where Country Name is in the list
    mask = df["Country Name"].isin(countries)
    
    filtered = df[mask].copy()
    
    print(f"[DEBUG FILTER COUNTRY] Filtered by {countries}: {len(filtered)} rows remain")
    
    return filtered