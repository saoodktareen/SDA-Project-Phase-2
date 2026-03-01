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

        if not region and self.config.get("continent"):
            region = self.config.get("continent")

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

        # ── CONTINENT VIEWS – always ALL continents, ignore country filter ──
        df_global = df_long.copy()  # full data, no country restriction

        # Top 10 & Bottom 10 – only from selected regions, single year
        if region and year:
            df_year = self._continent_filter(df_global, region)
            df_year = df_year[df_year["Year"] == year]
            top10 = df_year.nlargest(10, "GDP")[["Country Name", "GDP"]].round(2).to_dict("records")
            bottom10 = df_year.nsmallest(10, "GDP")[["Country Name", "GDP"]].round(2).to_dict("records")

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