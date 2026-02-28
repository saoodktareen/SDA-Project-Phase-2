def transform_to_long(cleaned_df):
    df_long = cleaned_df.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code", "Continent"],
        var_name="Year",
        value_name="GDP"
    )
    df_long["Year"] = df_long["Year"].astype(int)
    return df_long
