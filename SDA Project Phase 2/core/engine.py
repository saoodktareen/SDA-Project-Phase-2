from typing import List, Any
import pandas as pd
from .contracts import DataSink, PipelineService

class TransformationEngine(PipelineService):
    def __init__(self, sink: DataSink, analysis_config: dict):
        self.sink = sink
        self.config = analysis_config

    def execute(self, raw_data: List[Any]) -> None:
        df_long = pd.DataFrame(raw_data)  # already cleaned & in long format from Input

        results = []
        continent = self.config.get("continent")
        year = self.config.get("year")
        start_year = self.config.get("start_year")
        end_year = self.config.get("end_year")
        decline_years = self.config.get("decline_years", 5)

        # 1. Top 10 Countries
        if continent and year:
            df_year = df_long[(df_long["Continent"] == continent) & (df_long["Year"] == year)]
            top10 = df_year.nlargest(10, "GDP")[["Country Name", "GDP"]].round(2).to_dict("records")
            results.append({"type": "top10", "title": f"Top 10 Countries by GDP in {continent} ({year})", "data": top10})

        # 2. Bottom 10 Countries
        if continent and year:
            bottom10 = df_year.nsmallest(10, "GDP")[["Country Name", "GDP"]].round(2).to_dict("records")
            results.append({"type": "bottom10", "title": f"Bottom 10 Countries by GDP in {continent} ({year})", "data": bottom10})

        # 3. GDP Growth Rate of Each Country
        if continent and start_year and end_year and start_year != end_year:
            df_range = df_long[(df_long["Continent"] == continent) &
                               (df_long["Year"] >= start_year) & (df_long["Year"] <= end_year)]
            growth = df_range.groupby("Country Name")["GDP"].agg(["first", "last"]).reset_index()
            growth["growth_rate"] = ((growth["last"] - growth["first"]) / growth["first"] * 100).round(2)
            results.append({"type": "growth_rate", "title": f"GDP Growth Rate (%) in {continent} ({start_year}-{end_year})", "data": growth[["Country Name", "growth_rate"]].to_dict("records")})

        # 4. Average GDP by Continent
        if start_year and end_year:
            df_range = df_long[(df_long["Year"] >= start_year) & (df_long["Year"] <= end_year)]
            avg = df_range.groupby("Continent")["GDP"].mean().reset_index(name="Avg_GDP").round(2).to_dict("records")
            results.append({"type": "avg_continent", "title": f"Average GDP by Continent ({start_year}-{end_year})", "data": avg})

        # 5. Total Global GDP Trend
        if start_year and end_year:
            df_range = df_long[(df_long["Year"] >= start_year) & (df_long["Year"] <= end_year)]
            trend = df_range.groupby("Year")["GDP"].sum().reset_index(name="Total_GDP").round(2).to_dict("records")
            results.append({"type": "global_trend", "title": f"Total Global GDP Trend ({start_year}-{end_year})", "data": trend})

        # 6. Fastest Growing Continent
        if start_year and end_year and start_year != end_year:
            df_range = df_long[(df_long["Year"] >= start_year) & (df_long["Year"] <= end_year)]
            cont_growth = df_range.groupby("Continent")["GDP"].agg(["first", "last"]).reset_index()
            cont_growth["growth_rate"] = ((cont_growth["last"] - cont_growth["first"]) / cont_growth["first"] * 100).round(2)
            fastest = cont_growth.loc[cont_growth["growth_rate"].idxmax()].to_dict()
            results.append({"type": "fastest_continent", "title": f"Fastest Growing Continent ({start_year}-{end_year})", "data": [fastest]})

        # 7. Countries with Consistent GDP Decline
        if decline_years and end_year:
            start_decline = end_year - decline_years + 1
            df_decline = df_long[(df_long["Year"] >= start_decline) & (df_long["Year"] <= end_year)]
            decline_list = []
            for country, group in df_decline.groupby("Country Name"):
                sorted_gdp = group.sort_values("Year")["GDP"].tolist()
                if len(sorted_gdp) == decline_years and all(sorted_gdp[i] > sorted_gdp[i+1] for i in range(len(sorted_gdp)-1)):
                    decline_list.append({"Country Name": country, "Years": decline_years})
            results.append({"type": "decline", "title": f"Countries with Consistent GDP Decline (Last {decline_years} years up to {end_year})", "data": decline_list})

        # 8. Contribution of Each Continent
        if start_year and end_year:
            df_range = df_long[(df_long["Year"] >= start_year) & (df_long["Year"] <= end_year)]
            total_global = df_range["GDP"].sum()
            contrib = df_range.groupby("Continent")["GDP"].sum().reset_index()
            contrib["Contribution_%"] = (contrib["GDP"] / total_global * 100).round(2)
            results.append({"type": "contribution", "title": f"Continent Contribution to Global GDP ({start_year}-{end_year})", "data": contrib[["Continent", "Contribution_%"]].to_dict("records")})

        self.sink.write(results)