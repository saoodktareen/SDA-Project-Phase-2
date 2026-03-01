import altair as alt
import pandas as pd

PROFESSIONAL_PALETTE = [
    "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6",
    "#EF4444", "#06B6D4", "#EC4899", "#14B8A6"
]

HIGHLIGHT_COLOR = "#F59E0B"

def create_bar_chart(region_gdp: pd.DataFrame, focus_regions, year, operation):
    colors = region_gdp["Continent"].apply(lambda x: HIGHLIGHT_COLOR if x in focus_regions else PROFESSIONAL_PALETTE[0])
    return alt.Chart(region_gdp).mark_bar().encode(
        x=alt.X("Continent:N", sort="-y"),
        y="GDP:Q",
        color=alt.Color("Continent:N", scale=alt.Scale(range=colors.tolist())),
        tooltip=["Continent", "GDP"]
    ).properties(title=f"{operation.capitalize()} GDP by Region ({year}) – Bar", width=800, height=500)

def create_pie_chart(region_gdp: pd.DataFrame, focus_regions, year, operation):
    return alt.Chart(region_gdp).mark_arc().encode(
        theta="GDP:Q",
        color="Continent:N",
        tooltip=["Continent", "GDP"]
    ).properties(title=f"{operation.capitalize()} GDP Distribution ({year}) – Pie", width=500, height=500)

def create_heatmap(region_gdp: pd.DataFrame, focus_regions, year, operation):
    return alt.Chart(region_gdp).mark_rect().encode(
        x="Continent:N",
        y="GDP:Q",
        color="GDP:Q",
        tooltip=["Continent", "GDP"]
    ).properties(title=f"GDP Heatmap ({year})", width=800, height=400)

def get_region_charts(df: pd.DataFrame, config: Dict) -> Dict[str, callable]:
    years = config.get("year", [2020])
    focus_regions = config.get("region", []) or config.get("continent", [])
    operation = config.get("operation", "average")

    if df.empty:
        return {}

    charts = {}

    # Per year or average
    for year in years:
        region_gdp = df[df["Year"] == year].groupby("Continent")["GDP"].sum().reset_index()
        charts[f"Bar Chart ({year})"] = lambda rg=region_gdp, fr=focus_regions, y=year, op=operation: create_bar_chart(rg, fr, y, op)
        charts[f"Pie Chart ({year})"] = lambda rg=region_gdp, fr=focus_regions, y=year, op=operation: create_pie_chart(rg, fr, y, op)
        charts[f"Heatmap ({year})"] = lambda rg=region_gdp, fr=focus_regions, y=year, op=operation: create_heatmap(rg, fr, y, op)

    # For new analyses (e.g., contributions)
    if 'analyses' in config.get("analysis", {}) and "contributions" in config["analysis"]["analyses"]:
        charts["Contributions Pie"] = lambda: alt.Chart(df.groupby("Continent")["GDP"].sum().reset_index()).mark_arc().encode(theta='GDP', color='Continent')

    return charts