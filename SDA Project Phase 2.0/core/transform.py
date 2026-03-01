import pandas as pd

def transform_to_long(cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts wide-format GDP data to long format.
    If the DataFrame already contains a 'GDP' column (already long),
    it is returned as-is after ensuring the Year column is int.
    """
    # ── already in long format ─────────────────────────────────────────────
    if "GDP" in cleaned_df.columns:
        df = cleaned_df.copy()
        if "Year" in df.columns:
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
        return df

    # ── wide → long ────────────────────────────────────────────────────────
    id_cols = ["Country Name", "Country Code", "Indicator Name", "Indicator Code", "Continent"]

    # Only keep id_cols that actually exist in the dataframe
    existing_id_cols = [c for c in id_cols if c in cleaned_df.columns]

    df_long = cleaned_df.melt(
        id_vars=existing_id_cols,
        var_name="Year",
        value_name="GDP",
    )

    df_long["Year"] = pd.to_numeric(df_long["Year"], errors="coerce").astype("Int64")
    df_long = df_long.dropna(subset=["Year", "GDP"])
    df_long = df_long[df_long["GDP"] != 0]

    return df_long.reset_index(drop=True)