import altair as alt
import pandas as pd
import numpy as np
from functools import reduce

PROFESSIONAL_PALETTE = [
    "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6",
    "#EF4444", "#06B6D4", "#EC4899", "#14B8A6"
]

def prepare_country_data(df, countries, operation):
    aggregate_func = "sum" if operation == "sum" else "mean"
    return dict(
        map(
            lambda country: (
                country,
                df[df["Country Name"] == country]
                .groupby("Year")["GDP"]
                .agg(aggregate_func)
                .reset_index()
            ),
            countries
        )
    )

def create_line_chart(country_data):
    df_all = pd.concat([df.assign(Country=name) for name, df in country_data.items()])
    return alt.Chart(df_all).mark_line(point=True).encode(
        x="Year:O",
        y="GDP:Q",
        color="Country:N",
        tooltip=["Country", "Year", "GDP"]
    ).properties(title="GDP Trends – Line Chart", width=800, height=500)

def create_bar_chart(country_data, operation):
    df_mean = pd.DataFrame([
        {"Country": name, "Avg_GDP": df["GDP"].mean()} for name, df in country_data.items()
    ])
    return alt.Chart(df_mean).mark_bar().encode(
        x=alt.X("Country:N", sort="-y"),
        y="Avg_GDP:Q",
        color="Country:N",
        tooltip=["Country", "Avg_GDP"]
    ).properties(title=f"{operation.capitalize()} GDP by Country – Bar Chart", width=800, height=500)

def create_area_chart(country_data):
    df_all = pd.concat([df.assign(Country=name) for name, df in country_data.items()])
    return alt.Chart(df_all).mark_area(opacity=0.6).encode(
        x="Year:O",
        y="GDP:Q",
        color="Country:N",
        tooltip=["Country", "Year", "GDP"]
    ).properties(title="GDP Area Trends", width=800, height=500)

def create_scatter_chart(country_data):
    df_all = pd.concat([df.assign(Country=name) for name, df in country_data.items()])
    base = alt.Chart(df_all).mark_point(size=80).encode(
        x="Year:O",
        y="GDP:Q",
        color="Country:N",
        tooltip=["Country", "Year", "GDP"]
    )
    trend = base.transform_regression("Year", "GDP", groupby=["Country"]).mark_line()
    return (base + trend).properties(title="GDP Scatter + Trend", width=800, height=500)

def get_country_charts(df: pd.DataFrame, config: Dict) -> Dict[str, Callable[[], alt.Chart]]:
    """
    Returns dictionary of chart creation functions.
    Called in streamlit_app.py to populate sidebar dynamically.
    """
    countries = config.get("country", [])
    if not countries:
        return {}

    operation = config.get("operation", "average")
    country_data = prepare_country_data(df, countries, operation)

    return {
        "Line Chart": lambda: create_line_chart(country_data),
        "Bar Chart": lambda: create_bar_chart(country_data, operation),
        "Area Chart": lambda: create_area_chart(country_data),
        "Scatter + Trend": lambda: create_scatter_chart(country_data)
    }