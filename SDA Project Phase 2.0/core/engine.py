# File: core/engine.py
# Changes: Removed usage of "operation" (not present). Removed "decline_years" block. Removed config.get("continent") fallback. Fixed aggregations to use sum/mean internally as appropriate (no user-specified operation). Reconstructed full code based on provided truncated version, assuming standard logic for results generation.

from typing import List, Any
import pandas as pd
from .contracts import DataSink, PipelineService


class TransformationEngine(PipelineService):
    def __init__(self, sink: DataSink, analysis_config: dict):
        self.sink = sink
        self.config = analysis_config

    @staticmethod
    def _continent_filter(df: pd.DataFrame, region) -> pd.DataFrame:
        if not region:
            return df
        if isinstance(region, list):
            return df[df["Continent"].isin(region)]
        return df[df["Continent"] == region]

    @staticmethod
    def _country_filter(df: pd.DataFrame, country) -> pd.DataFrame:
        if not country:
            return df
        if isinstance(country, list):
            return df[df["Country Name"].isin(country)]
        return df[df["Country Name"] == country]

    def execute(self, raw_data: List[Any]) -> None:
        df_long = pd.DataFrame(raw_data)
        df_long["Year"] = df_long["Year"].astype(int)

        results = []
        region = self.config.get("region")
        year = self.config.get("year")
        start_year = self.config.get("start_year")
        end_year = self.config.get("end_year")
        countries = self.config.get("country")

        region_label = ", ".join(region) if isinstance(region, list) else (region or "All")
        has_countries = bool(countries)

        # ── COUNTRY VIEWS ───────────────────────────────────────────────────
        if has_countries:
            df_countries = self._country_filter(df_long, countries)

            # Growth Rate – only for selected countries (multi-line ready)
            if start_year and end_year and start_year != end_year:
                df_range = df_countries[
                    (df_countries["Year"] >= start_year) & (df_countries["Year"] <= end_year)
                ]
                trend_lines = df_range.pivot_table(
                    index="Year", columns="Country Name", values="GDP", aggfunc="sum"
                ).fillna(0).reset_index()
                results.append({
                    "type": "growth_rate",
                    "title": f"GDP Growth Rate (%) – Selected Countries ({start_year}–{end_year})",
                    "data": trend_lines.to_dict("records"),
                })

        # ── CONTINENT VIEWS – always include ────────────────────────────────
        df_global = df_long.copy()  # For global aggregates

        if region:
            df_filtered = self._continent_filter(df_long, region)
        else:
            df_filtered = df_long

        # Top/Bottom 10 by GDP for specific year (sum implied)
        if year:
            df_year = df_filtered[df_filtered["Year"] == year]
            country_gdp = df_year.groupby("Country Name")["GDP"].sum().reset_index().sort_values("GDP", ascending=False).round(2)
            top10 = country_gdp.head(10).to_dict("records")
            bottom10 = country_gdp.tail(10).to_dict("records")
            results.append({"type": "top10", "title": f"Top 10 Countries by GDP in {region_label} ({year})", "data": top10})
            results.append({"type": "bottom10", "title": f"Bottom 10 Countries by GDP in {region_label} ({year})", "data": bottom10})

        # Average GDP by Continent – ALL continents alphabetical
        if start_year and end_year:
            df_range = df_global[(df_global["Year"] >= start_year) & (df_global["Year"] <= end_year)]
            avg = df_range.groupby("Continent")["GDP"].mean().reset_index(name="Avg_GDP").round(2)
            avg = avg.sort_values("Continent")  # alphabetical
            avg["is_selected"] = avg["Continent"].isin(region if isinstance(region, list) else [region])
            results.append({
                "type": "avg_continent",
                "title": f"Average GDP by Continent ({start_year}–{end_year})",
                "data": avg.to_dict("records"),
            })

        # Total GDP by Continent – ALL continents alphabetical
        if start_year and end_year:
            df_range = df_global[(df_global["Year"] >= start_year) & (df_global["Year"] <= end_year)]
            total = df_range.groupby("Continent")["GDP"].sum().reset_index(name="Total_GDP").round(2)
            total = total.sort_values("Continent")
            total["is_selected"] = total["Continent"].isin(region if isinstance(region, list) else [region])
            results.append({
                "type": "total_gdp_continent",
                "title": f"Total GDP by Continent ({start_year}–{end_year})",
                "data": total.to_dict("records"),
            })

        # Continent Contribution – ALL continents alphabetical
        if start_year and end_year:
            df_range = df_global[(df_global["Year"] >= start_year) & (df_global["Year"] <= end_year)]
            total_global = df_range["GDP"].sum()
            contrib = df_range.groupby("Continent")["GDP"].sum().reset_index()
            contrib["Contribution_%"] = (contrib["GDP"] / total_global * 100).round(2)
            contrib = contrib.sort_values("Continent")
            contrib["is_selected"] = contrib["Continent"].isin(region if isinstance(region, list) else [region])
            results.append({
                "type": "contribution",
                "title": f"Continent Contribution to Global GDP ({start_year}–{end_year})",
                "data": contrib[["Continent", "Contribution_%", "is_selected"]].to_dict("records"),
            })

        self.sink.write(results)