import pandas as pd

def validate_json(config: dict, clean_df: pd.DataFrame):
    errors = []

    required_keys = {"operation", "output", "country", "region", "year"}

    # ---------- 1. STRUCTURE CHECK ----------
    if not isinstance(config, dict):
        return None, ["JSON must be a dictionary"]

    missing_keys = required_keys - config.keys()
    extra_keys = config.keys() - required_keys

    errors += list(map(lambda k: f"Missing keys: {list(missing_keys)}", missing_keys))
    errors += list(map(lambda k: f"Extra keys not allowed: {list(extra_keys)}", extra_keys))

    # ---------- 2. NULL / EMPTY CHECK ----------
    def validate_value(item):
        key, value = item
        if value is None:
            return f"'{key}' cannot be null"
        if isinstance(value, str) and not value.strip():
            return f"'{key}' cannot be empty"
        if isinstance(value, list) and not value:
            return f"'{key}' list cannot be empty"
        return None

    errors += list(
        filter(
            None,
            map(validate_value, map(lambda k: (k, config.get(k)), required_keys))
        )
    )

    # ---------- 3. OPERATION ----------
    operation = str(config.get("operation", "")).lower()
    if operation not in {"sum", "average"}:
        errors.append("Operation must be 'sum' or 'average'")

    # ---------- 4. OUTPUT ----------
    output = str(config.get("output", "")).lower()
    if output != "dashboard":
        errors.append("Output must be 'dashboard'")

    # ---------- 5. DF REFERENCES ----------
    df_countries = set(clean_df["Country Name"].str.strip())
    df_regions = set(clean_df["Continent"].str.strip())
    df_years = {int(col) for col in clean_df.columns if col.isdigit()}

    # ---------- 6. COUNTRY ----------
    countries = config.get("country", [])
    countries = [countries] if isinstance(countries, str) else countries

    invalid_countries = list(filter(lambda c: c not in df_countries, countries))
    if invalid_countries:
        errors.append(f"Invalid country names: {invalid_countries}")

    # ---------- 7. REGION ----------
    regions = config.get("region", [])
    regions = [regions] if isinstance(regions, str) else regions

    invalid_regions = list(filter(lambda r: r not in df_regions, regions))
    if invalid_regions:
        errors.append(f"Invalid regions: {invalid_regions}")

    # ---------- 8. YEAR ----------
    years = config.get("year", [])
    years = [years] if isinstance(years, int) else years

    invalid_years = list(
        filter(
            lambda y: not isinstance(y, int) or y not in df_years or y < 1960 or y > 2024,
            years
        )
    )

    if invalid_years:
        errors.append(f"Invalid years: {invalid_years}")

    # ---------- 9. RETURN ----------
    if errors:
        return None, errors

    validated = {
        "operation": operation,
        "output": output,
        "country": countries,
        "region": regions,
        "year": years
    }

    return validated, []
