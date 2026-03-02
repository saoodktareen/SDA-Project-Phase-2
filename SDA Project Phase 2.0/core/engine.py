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
        decline_years = self.config.get("decline_years")

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

        # ── Consistent GDP Decline Check – Show ALL selected countries ──
        if decline_years is not None:
            decline_n = int(decline_years)

            # Use only selected countries (fallback to region or all)
            df_check = df_long.copy()
            if countries:
                df_check = self._country_filter(df_check, countries)
            elif region:
                df_check = self._continent_filter(df_check, region)

            # Determine the period: prefer end_year, fallback to latest year
            end_y = end_year if end_year else df_check["Year"].max()
            start_y = end_y - decline_n + 1

            if start_y < df_check["Year"].min():
                start_y = df_check["Year"].min()  # adjust to available data

            decline_countries_data = []

            # Process every selected country
            for country in df_check["Country Name"].unique():
                country_df = df_check[(df_check["Country Name"] == country) &
                                     (df_check["Year"] >= start_y) &
                                     (df_check["Year"] <= end_y)]

                # Get actual number of years available
                actual_years = len(country_df)
                if actual_years < 2:
                    continue  # not enough data points

                # Sort and check if strict decline
                sorted_df = country_df.sort_values("Year")
                gdp_values = sorted_df["GDP"].values
                is_decline = all(gdp_values[i] > gdp_values[i+1] for i in range(len(gdp_values)-1))

                # Prepare chart data (show all available years in period + some context)
                chart_df = sorted_df[["Year", "GDP"]]
                # Add 5 previous years if available for context
                context_start = max(df_check["Year"].min(), start_y - 5)
                context_df = df_check[(df_check["Country Name"] == country) &
                                     (df_check["Year"] >= context_start) &
                                     (df_check["Year"] < start_y)]
                chart_df = pd.concat([context_df[["Year", "GDP"]], chart_df]).sort_values("Year")

                decline_countries_data.append({
                    "country": country,
                    "decline_years_requested": decline_n,
                    "years_checked": actual_years,
                    "start_year": int(sorted_df["Year"].min()),
                    "end_year": int(sorted_df["Year"].max()),
                    "is_decline": is_decline,
                    "chart_data": chart_df.to_dict("records")
                })

            if decline_countries_data:
                results.append({
                    "type": "decline",
                    "title": f"GDP Trend – Last {decline_n} Years ({start_y}–{end_y}) for Selected Countries",
                    "data": decline_countries_data
                })
            
        # Fastest Growing Continent for the given date range ──
        if start_year and end_year and start_year != end_year:
            df_range = df_global[(df_global["Year"] >= start_year) & (df_global["Year"] <= end_year)]

            # Calculate total GDP at start and end year per continent
            gdp_start = df_range[df_range["Year"] == start_year].groupby("Continent")["GDP"].sum().reset_index(name="GDP_Start")
            gdp_end   = df_range[df_range["Year"] == end_year].groupby("Continent")["GDP"].sum().reset_index(name="GDP_End")

            # Merge start and end GDP
            growth = pd.merge(gdp_start, gdp_end, on="Continent", how="outer").fillna(0)

            # Calculate growth rate (avoid division by zero)
            growth["Growth_Rate_%"] = ((growth["GDP_End"] - growth["GDP_Start"]) / growth["GDP_Start"].replace(0, float('inf')) * 100).round(2)
            growth["Growth_Rate_%"] = growth["Growth_Rate_%"].replace([float('inf'), -float('inf')], 0)

            # Find the continent with highest growth rate
            if not growth.empty:
                fastest = growth.loc[growth["Growth_Rate_%"].idxmax()]

                fastest_data = {
                    "Continent": fastest["Continent"],
                    "Start_GDP": round(fastest["GDP_Start"], 2),
                    "End_GDP": round(fastest["GDP_End"], 2),
                    "Growth_Rate_%": fastest["Growth_Rate_%"],
                    "Period": f"{start_year}–{end_year}"
                }

                results.append({
                    "type": "fastest_growing_continent",
                    "title": f"Fastest Growing Continent ({start_year}–{end_year})",
                    "data": [fastest_data]  # single item list
                })
        # ── Write all results to sink ────────────────────────────────────
        self.sink.write(results)