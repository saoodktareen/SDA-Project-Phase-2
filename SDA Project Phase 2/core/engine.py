from typing import List, Any, Dict
import pandas as pd
import numpy as np

from .contracts import DataSink, PipelineService
from .cleaner import clean_data
from .transform import transform_to_long
from .filter_by_region import filter_by_region
from .filter_by_country import filter_by_country
from .process import process
from .validate_json import validate_json  # For cross-check

class TransformationEngine(PipelineService):
    def __init__(self, sink: DataSink, config: Dict[str, Any]):
        self.sink = sink
        self.config = config

    def execute(self, raw_data: List[Dict[str, Any]]) -> None:
        print(f"[ENGINE] Received {len(raw_data)} raw records")

        if not raw_data:
            self._send_error("No data received from input")
            return

        df_wide = pd.DataFrame(raw_data)
        cleaned_wide, error_log = clean_data(df_wide)

        if any(v for v in error_log.values()):
            self.sink.write([{
                "type": "errors",
                "title": "Cleaning Report",
                "data": [f"{k}: {v}" for k, v in error_log.items() if v]
            }])

        # Cross-validate config with cleaned DF (Phase 1 restore)
        validated_config, val_errors = validate_json(self.config, cleaned_wide)  # Pass DF
        if val_errors:
            self._send_error("\n".join(val_errors))
            return
        self.config = validated_config  # Update if needed

        df_long = transform_to_long(cleaned_wide)

        # Year filter (Phase 1/2)
        years = self.config.get("year", [])
        if years:
            years = years if isinstance(years, list) else [years]
            df_long = df_long[df_long["Year"].isin(years)]

        df_filtered = filter_by_region(df_long, self.config)
        # Phase 1 special: If single continent and no countries, auto-include all countries
        continents = self.config.get("continent", []) or self.config.get("region", [])
        countries = self.config.get("country", [])
        if len(continents) == 1 and not countries:
            self.config["country"] = df_filtered["Country Name"].unique().tolist()
        df_filtered = filter_by_country(df_filtered, self.config)

        op = self.config.get("operation", "average")

        region_df = process(df_filtered, self.config, "Continent")
        country_df = process(df_filtered, self.config, "Country Name")
        yearly_df = df_filtered.groupby("Year")["GDP"].agg(op).reset_index(name="GDP")

        results = [
            {"type": "region_agg", "title": f"{op.capitalize()} GDP by Continent", "data": region_df.to_dict("records")},
            {"type": "country_agg", "title": f"{op.capitalize()} GDP by Country", "data": country_df.to_dict("records")},
            {"type": "yearly_trend", "title": f"{op.capitalize()} GDP Trend Over Years", "data": yearly_df.to_dict("records")},
            {"type": "raw_preview", "title": "Preview of Filtered Long Data (first 200 rows)", "data": df_filtered.head(200).to_dict("records")}
        ]

        # Phase 2 new analyses
        analyses = self.config.get("analysis", {}).get("analyses", [])
        start_year = self.config.get("analysis", {}).get("start_year", 1960)
        end_year = self.config.get("analysis", {}).get("end_year", 2024)
        decline_years = self.config.get("analysis", {}).get("decline_years", 3)
        top_n = self.config.get("analysis", {}).get("top_n", 10)

        if "top10" in analyses:
            top_df = self.calculate_top_n(df_filtered, top_n, continents[0] if continents else None, end_year)
            results.append({"type": "top10", "title": f"Top {top_n} Countries", "data": top_df.to_dict("records")})

        if "bottom10" in analyses:
            bottom_df = self.calculate_bottom_n(df_filtered, top_n, continents[0] if continents else None, end_year)
            results.append({"type": "bottom10", "title": f"Bottom {top_n} Countries", "data": bottom_df.to_dict("records")})

        if "growth_rates" in analyses:
            growth_df = self.calculate_growth_rates(df_filtered, start_year, end_year)
            results.append({"type": "growth_rates", "title": "Growth Rates", "data": growth_df.to_dict("records")})

        if "averages" in analyses:
            avgs_df = self.calculate_averages(df_filtered)
            results.append({"type": "averages", "title": "Averages per Continent/Year", "data": avgs_df.to_dict("records")})

        if "trends" in analyses:
            trends_df = self.calculate_trends(df_filtered)
            results.append({"type": "trends", "title": "GDP Trends", "data": trends_df.to_dict("records")})

        if "fastest_growing" in analyses:
            fastest_df = self.calculate_fastest_growing(df_filtered, start_year, end_year)
            results.append({"type": "fastest_growing", "title": "Fastest Growing Continents", "data": fastest_df.to_dict("records")})

        if "declines" in analyses:
            declines_df = self.calculate_declines(df_filtered, decline_years)
            results.append({"type": "declines", "title": "Declining Countries", "data": declines_df.to_dict("records")})

        if "contributions" in analyses:
            contrib_df = self.calculate_contributions(df_filtered, end_year)
            results.append({"type": "contributions", "title": "Continent Contributions", "data": contrib_df.to_dict("records")})

        print(f"[ENGINE] Sending {len(results)} result blocks")
        self.sink.write(results)

    def _send_error(self, msg: str):
        self.sink.write([{"type": "errors", "title": "Processing Error", "data": [msg]}])

    # New Phase 2 analysis methods (functional style where possible)
    def calculate_top_n(self, df: pd.DataFrame, n: int, continent: str, year: int):
        filtered = df[(df['Continent'] == continent) & (df['Year'] == year)] if continent else df[df['Year'] == year]
        return filtered.nlargest(n, 'GDP')[['Country Name', 'GDP', 'Continent']]

    def calculate_bottom_n(self, df: pd.DataFrame, n: int, continent: str, year: int):
        filtered = df[(df['Continent'] == continent) & (df['Year'] == year)] if continent else df[df['Year'] == year]
        return filtered.nsmallest(n, 'GDP')[['Country Name', 'GDP', 'Continent']]

    def calculate_growth_rates(self, df: pd.DataFrame, start: int, end: int):
        df = df[(df['Year'] >= start) & (df['Year'] <= end)]
        growth = df.groupby('Continent').apply(lambda g: g.sort_values('Year').assign(Growth_Rate=lambda x: x['GDP'].pct_change() * 100))
        return growth.reset_index(drop=True)

    def calculate_averages(self, df: pd.DataFrame):
        return df.groupby(['Continent', 'Year'])['GDP'].mean().reset_index(name='Average GDP')

    def calculate_trends(self, df: pd.DataFrame):
        return df.groupby(['Continent', 'Year'])['GDP'].mean().rolling(window=3).mean().reset_index(0, drop=True).reset_index(name='Trend GDP')

    def calculate_fastest_growing(self, df: pd.DataFrame, start: int, end: int):
        growth = self.calculate_growth_rates(df, start, end)
        return growth.groupby('Continent')['Growth_Rate'].mean().nlargest(1).reset_index()

    def calculate_declines(self, df: pd.DataFrame, years: int):
        def has_decline(g):
            g = g.sort_values('Year')
            declines = (g['GDP'].pct_change() < 0).rolling(years).sum() >= years
            return declines.any()
        declines = df.groupby('Country Name').apply(has_decline)
        return df[df['Country Name'].isin(declines[declines].index)][['Country Name', 'Year', 'GDP']].drop_duplicates('Country Name')

    def calculate_contributions(self, df: pd.DataFrame, year: int):
        yearly = df[df['Year'] == year]
        total = yearly['GDP'].sum()
        contrib = yearly.groupby('Continent')['GDP'].sum() / total * 100
        return contrib.reset_index(name='Contribution %')