import pandas as pd

def clean_data(df: pd.DataFrame):
    # Work on a copy
    df = df.copy()

    # ---------- ERROR LOG ----------
    error_log = {
        "text_errors": [],
        "empty_country": [],
        "gdp_alpha": [],
        "empty_gdp": [],
        "invalid_continent": []
    }

    # Text columns
    text_cols = [
        "Country Name",
        "Country Code",
        "Indicator Name",
        "Indicator Code",
        "Continent"
    ]

    # GDP columns
    gdp_cols = df.columns.difference(text_cols)

    # ---------- REMOVE DUPLICATES ----------
    df = df.drop_duplicates()

    # ---------- TEXT CLEANING ----------
    df[text_cols] = df[text_cols].astype("string").fillna("")

    # ---------- TEXT VALIDATION ----------
    bad_text_rows = df[text_cols].apply(
        lambda c: c.str.contains(r"\d")
    ).any(axis=1)

    error_log["text_errors"] = (df.index[bad_text_rows] + 2).tolist()
    df = df[~bad_text_rows]

    # ---------- EMPTY COUNTRY ----------
    bad_country_rows = df["Country Name"].str.strip().eq("")
    error_log["empty_country"] = (df.index[bad_country_rows] + 2).tolist()
    df = df[~bad_country_rows]

    # ---------- GDP LETTER CHECK ----------
    # First convert to numeric 
    gdp_original = df[gdp_cols].copy()
    gdp_numeric = df[gdp_cols].apply(pd.to_numeric, errors="coerce")
    
    # Find cells that were not originally empty
    was_not_empty = gdp_original.notna()
    
    # Find cells that became NaN after numeric conversion
    became_nan = gdp_numeric.isna()
    
    # Cells with invalid data are those that had values but became NaN
    has_invalid_data = was_not_empty & became_nan
    bad_gdp_rows = has_invalid_data.any(axis=1)

    error_log["corrected_gdp"] = (df.index[bad_gdp_rows] + 2).tolist()

    # Print corrected GDP rows to terminal
    if bad_gdp_rows.any():
        print("\n" + "="*60)
        print("⚠️  GDP CORRECTION REPORT")
        print("="*60)
        corrected_rows = (df.index[bad_gdp_rows] + 2).tolist()
        print(f"The following rows had invalid GDP values and were corrected to 0.00:")
        print(f"Row Numbers: {corrected_rows}")
        print("="*60 + "\n")

    # Use the already-converted numeric data
    df[gdp_cols] = gdp_numeric.fillna(0.0).astype(float)

    # ---------- EMPTY GDP ----------
    empty_gdp_rows = (df[gdp_cols] == 0).all(axis=1)
    error_log["empty_gdp"] = (df.index[empty_gdp_rows] + 2).tolist()
    df = df[~empty_gdp_rows]

    # ---------- CONTINENT VALIDATION ----------
    valid_continents = {
        "Asia", "Europe", "Africa",
        "North America", "South America",
        "Oceania", "Global"
    }

    bad_continent_rows = ~df["Continent"].isin(valid_continents)
    error_log["invalid_continent"] = (df.index[bad_continent_rows] + 2).tolist()
    df = df[~bad_continent_rows]

    # ---------- RETURN ----------
    return df.reset_index(drop=True), error_log