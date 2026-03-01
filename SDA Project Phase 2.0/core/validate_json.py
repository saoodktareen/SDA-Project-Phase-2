# File: core/validate_json.py
# Changes: Updated required keys to region, country, start_year, end_year (year optional). Removed operation, output. Handle region/country as str or list. Validate years 1960-2024, start <= end. Check against clean_df uniques. No checks for df_years presence, only range.

import pandas as pd

def validate_json(config: dict, clean_df: pd.DataFrame):
    errors = []

    required_keys = {"region", "country", "start_year", "end_year"}

    if not isinstance(config, dict):
        return None, ["Config must be a dictionary"]

    missing_keys = required_keys - config.keys()
    if missing_keys:
        errors.append(f"Missing required keys: {list(missing_keys)}")

    # NULL / EMPTY CHECK
    for key in required_keys:
        value = config.get(key)
        if value is None:
            errors.append(f"'{key}' cannot be null")
        elif isinstance(value, list) and not value:
            pass  # Allow empty lists (means all)
        elif isinstance(value, str) and not value.strip():
            errors.append(f"'{key}' cannot be empty string")

    # REGION
    region = config.get("region")
    if region is not None:
        if not isinstance(region, (str, list)):
            errors.append("'region' must be string or list")
        else:
            regions = [region] if isinstance(region, str) else region
            df_regions = set(clean_df["Continent"].dropna().unique())
            invalid_regions = set(regions) - df_regions
            if invalid_regions:
                errors.append(f"Invalid regions: {list(invalid_regions)}")

    # COUNTRY
    country = config.get("country")
    if country is not None:
        if not isinstance(country, (str, list)):
            errors.append("'country' must be string or list")
        else:
            countries = [country] if isinstance(country, str) else country
            df_countries = set(clean_df["Country Name"].dropna().unique())
            invalid_countries = set(countries) - df_countries
            if invalid_countries:
                errors.append(f"Invalid countries: {list(invalid_countries)}")

    # START_YEAR, END_YEAR
    start_year = config.get("start_year")
    end_year = config.get("end_year")
    if isinstance(start_year, int) and isinstance(end_year, int):
        if not (1960 <= start_year <= 2024):
            errors.append("start_year must be between 1960 and 2024")
        if not (1960 <= end_year <= 2024):
            errors.append("end_year must be between 1960 and 2024")
        if start_year > end_year:
            errors.append("start_year must be <= end_year")
    else:
        if start_year is not None and not isinstance(start_year, int):
            errors.append("start_year must be integer")
        if end_year is not None and not isinstance(end_year, int):
            errors.append("end_year must be integer")

    # YEAR (optional)
    year = config.get("year")
    if year is not None:
        if not isinstance(year, int):
            errors.append("year must be integer")
        elif not (1960 <= year <= 2024):
            errors.append("year must be between 1960 and 2024")

    if errors:
        return None, errors

    # Normalize to lists
    validated = config.copy()
    if isinstance(validated.get("region"), str):
        validated["region"] = [validated["region"]]
    if isinstance(validated.get("country"), str):
        validated["country"] = [validated["country"]]

    return validated, []