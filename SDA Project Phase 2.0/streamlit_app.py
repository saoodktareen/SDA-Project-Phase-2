import streamlit as st
import pandas as pd
import json
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import TransformationEngine
from core.cleaner import clean_data
from core.transform import transform_to_long
from core.contracts import DataSink

class StreamlitSink(DataSink):
    def write(self, records: list[dict]) -> None:
        st.session_state["results"] = records

# Initialize session state
for key, default in [
    ("step", "input"),
    ("results", []),
    ("data", None),
    ("raw_data_wide", None),
    ("raw_errors", {}),
    ("config", {}),
    ("analysis_mode", "upload"),  # "upload" or "manual"
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ────────────────────────────────────────────────
# INPUT PAGE
# ────────────────────────────────────────────────
if st.session_state["step"] == "input":
    st.title("🌍 World GDP Analysis Dashboard")
    st.markdown("Upload CSV (always required) and choose analysis mode")

    # ── Raw Data Upload – now accepts BOTH CSV and JSON (wide format) ──
    st.subheader("Upload raw data file (CSV or JSON)")
    uploaded_raw = st.file_uploader("Choose raw data file", type=["csv", "json"], key="raw_data_upload")

    if uploaded_raw is not None:
        try:
            if uploaded_raw.name.lower().endswith(".csv"):
                df_wide = pd.read_csv(uploaded_raw)
            elif uploaded_raw.name.lower().endswith(".json"):
                raw_data = json.load(uploaded_raw)
                if not isinstance(raw_data, list):
                    raise ValueError("JSON raw data must be a list of country records (wide format like your attached file)")
                df_wide = pd.DataFrame(raw_data)
            else:
                raise ValueError("Only .csv and .json files are supported for raw data.")

            df_wide, errors = clean_data(df_wide)
            st.success(f"Raw data loaded & cleaned: {len(df_wide)} rows")
            st.session_state["raw_data_wide"] = df_wide
            if len(df_wide) > 0:
                df_long = transform_to_long(df_wide)
                st.session_state["data"] = df_long
                st.session_state["raw_errors"] = errors
        except Exception as e:
            st.error(f"Error loading raw data file: {str(e)}")

    # ── Mode selection ──
    st.divider()
    st.subheader("Choose how to run the analysis")

    mode = st.radio(
        "Analysis mode",
        options=[
            "Use uploaded data (CSV or JSON) – ignore manual settings",
            "Use manual configuration (regions, countries, years, etc.)"
        ],
        index=0 if st.session_state["analysis_mode"] == "upload" else 1,
        key="analysis_mode_radio"
    )

    is_upload_mode = "uploaded data" in mode
    st.session_state["analysis_mode"] = "upload" if is_upload_mode else "manual"

    # ── JSON Config Upload – only available in upload mode ──
    if is_upload_mode:
        st.subheader("Upload JSON file (optional)")
        uploaded_json = st.file_uploader("Choose JSON file", type="json", key="json_upload")
        if uploaded_json is not None:
            try:
                loaded = json.load(uploaded_json)

                # ── If it has "analysis" key → it's config ──────────────
                if isinstance(loaded, dict) and "analysis" in loaded:
                    analysis = loaded["analysis"]
                    st.success("Configuration JSON detected! Validating and using settings from file.")

                    # ── Validate the config ──────────────────────────────
                    if st.session_state.get("data") is None:
                        st.error("Please upload raw data first for validation.")
                    else:
                        clean_df = st.session_state["raw_data_wide"]

                        errors = []

                        required_keys = {"country", "region", "year", "start_year", "end_year"}
                        missing_keys = required_keys - analysis.keys()
                        if missing_keys:
                            errors.append(f"Missing keys: {list(missing_keys)}")

                        for k, v in analysis.items():
                            if v is None:
                                errors.append(f"'{k}' cannot be null")
                            if isinstance(v, str) and not v.strip():
                                errors.append(f"'{k}' cannot be empty")
                            if isinstance(v, list) and not v:
                                errors.append(f"'{k}' list cannot be empty")

                        df_countries = set(clean_df["Country Name"].str.strip())
                        df_regions = set(clean_df["Continent"].str.strip())
                        df_years = {int(col) for col in clean_df.columns if col.isdigit()}

                        countries = analysis.get("country", [])
                        countries = [countries] if isinstance(countries, str) else countries
                        invalid_countries = [c for c in countries if c not in df_countries]
                        if invalid_countries:
                            errors.append(f"Invalid country names: {invalid_countries}")

                        regions = analysis.get("region", [])
                        regions = [regions] if isinstance(regions, str) else regions
                        invalid_regions = [r for r in regions if r not in df_regions]
                        if invalid_regions:
                            errors.append(f"Invalid regions: {invalid_regions}")

                        year = analysis.get("year")
                        if year is not None and not 1960 <= year <= 2024:
                            errors.append(f"Invalid year: {year} (must be 1960-2024)")

                        start_year = analysis.get("start_year")
                        end_year = analysis.get("end_year")
                        if start_year is not None and end_year is not None:
                            if not 1960 <= start_year <= 2024 or not 1960 <= end_year <= 2024 or start_year > end_year:
                                errors.append(f"Invalid year range: start {start_year}, end {end_year} (must be 1960-2024 and start <= end)")

                        input_type = loaded.get("input_type")
                        if input_type not in ["csv", "json"]:
                            errors.append(f"Invalid input_type: {input_type} (must be 'csv' or 'json')")

                        output_type = loaded.get("output_type")
                        if output_type not in ["graphics", "console"]:
                            errors.append(f"Invalid output_type: {output_type} (must be 'graphics' or 'console')")

                        if errors:
                            for err in errors:
                                st.error(err)
                            st.stop()
                        else:
                            st.success("JSON config validated successfully!")

                            config_from_json = {
                                "region": analysis.get("region"),
                                "country": analysis.get("country"),
                                "year": analysis.get("year"),
                                "start_year": analysis.get("start_year"),
                                "end_year": analysis.get("end_year"),
                                "decline_years": analysis.get("decline_years"),
                                "operation": analysis.get("operation", "sum"),
                            }

                            st.session_state["config"] = config_from_json

                            if st.session_state.get("data") is not None:
                                df = st.session_state["data"].copy()
                                df["Year"] = df["Year"].astype(int)
                                sink = StreamlitSink()
                                engine = TransformationEngine(sink, config_from_json)
                                engine.execute(df.to_dict("records"))
                                st.session_state["step"] = "dashboard"
                                st.rerun()
                            else:
                                st.info("Config loaded. Upload raw data to run analysis.")

                else:
                    st.warning("This uploader is for config JSON files (with 'analysis' key). "
                               "Raw data should be uploaded in the top uploader.")
            except Exception as e:
                st.error(f"Error loading JSON: {e}")

    # ── Show data quality if data exists ──
    if st.session_state.get("data") is not None:
        st.divider()
        st.subheader("Data Quality Summary")
        errors = st.session_state.get("raw_errors", {})
        if any(len(v) > 0 for v in errors.values()):
            for k, v in errors.items():
                if v:
                    st.warning(f"{k.replace('_',' ').title()}: {len(v)} issues")
        else:
            st.success("Data looks clean ✓")

    # ── Analysis Settings ──
    st.divider()
    st.subheader("Analysis Settings")

    all_countries = []
    if st.session_state.get("data") is not None:
        try:
            all_countries = sorted(
                st.session_state["data"]["Country Name"].dropna().unique().tolist()
            )
        except KeyError:
            st.warning("Could not find 'Country Name' column in data.")

    if is_upload_mode:
        st.info("Manual configuration is disabled in this mode.\n"
                "The analysis will use the full uploaded dataset.")

        st.text_input("Regions / Continents", value="All", disabled=True)
        st.text_input("Countries", value="All", disabled=True)
        st.number_input("Single Target Year", disabled=True)
        st.number_input("Start Year", disabled=True)
        st.number_input("End Year", disabled=True)

        regions = None
        selected_countries = None
        target_year = None
        start_year = None
        end_year = None
        decline_years = None

    else:
        with st.form(key="manual_analysis_form"):
            col1, col2 = st.columns(2)

            with col1:
                regions = st.multiselect(
                    "Regions / Continents",
                    options=["Asia", "Europe", "Africa", "North America", "South America", "Oceania", "Global"],
                    default=[]
                )

                selected_countries = st.multiselect(
                    "Countries (optional – shows growth rate)",
                    options=all_countries,
                    default=[]
                )

                target_year = st.number_input(
                    "Single Target Year (for Top/Bottom 10)",
                    1960, 2024,
                    value=None,
                    step=1,
                    format="%d"
                )

            with col2:
                start_year = st.number_input(
                    "Start Year",
                    1960, 2024,
                    value=None,
                    step=1,
                    format="%d"
                )

                end_year = st.number_input(
                    "End Year",
                    1960, 2024,
                    value=None,
                    step=1,
                    format="%d"
                )

                decline_years = st.number_input(
                    "Years of Consistent GDP Decline",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1,
                    format="%d",
                    help="Number of consecutive recent years to check for GDP decline per country"
                )

            submitted = st.form_submit_button("Run Analysis", use_container_width=True)

    if is_upload_mode:
        run_button = st.button("Run Analysis", use_container_width=True, type="primary")
        submitted = run_button
    else:
        submitted = 'submitted' in locals() and submitted

    if 'submitted' in locals() and submitted:
        if st.session_state.get("data") is None:
            st.error("No data loaded. Please upload at least a CSV or JSON raw data file first.")
            st.stop()

        if not is_upload_mode:
            has_input = bool(regions) or bool(selected_countries) or \
                        (start_year is not None and end_year is not None)

            if not has_input:
                st.warning("In manual mode please select at least one region or country, "
                           "or provide a valid year range.")
                st.stop()

            if start_year is not None and end_year is not None:
                if start_year > end_year:
                    st.error("Start Year cannot be greater than End Year.")
                    st.stop()

        config = {
            "region": regions if regions else None,
            "country": selected_countries if selected_countries else None,
            "year": int(target_year) if target_year is not None else None,
            "start_year": int(start_year) if start_year is not None else None,
            "end_year": int(end_year) if end_year is not None else None,
            "decline_years": decline_years if decline_years is not None else None,
            "operation": "sum",
        }

        st.session_state["config"] = config

        df = st.session_state["data"].copy()
        df["Year"] = df["Year"].astype(int)

        sink = StreamlitSink()
        engine = TransformationEngine(sink, config)
        engine.execute(df.to_dict("records"))

        st.session_state["step"] = "dashboard"
        st.rerun()

# ────────────────────────────────────────────────
# DASHBOARD PAGE
# ────────────────────────────────────────────────
else:
    st.title("🌍 GDP Analysis Dashboard – Results")
    st.markdown("Select a visualization from the sidebar")

    with st.sidebar:
        st.subheader("Visualizations")
        results = st.session_state.get("results", [])
        titles = [r.get("title", f"View {i+1}") for i, r in enumerate(results)]
        selected_title = st.radio("Select view:", titles if titles else ["No results"])

        if st.button("← Back to Input"):
            st.session_state["step"] = "input"
            st.rerun()

    if not results:
        st.info("No results yet. Run an analysis first.")
    else:
        selected = next((r for r in results if r.get("title") == selected_title), None)
        if selected:
            st.subheader(selected.get("title", "Result"))
            data = selected.get("data", [])
            typ = selected.get("type", "")

            if data:
                df = pd.DataFrame(data)

                with st.expander("Raw Data Table", expanded=False):
                    st.dataframe(df, use_container_width=True)

                SELECTED_COLOR = "#F59E0B"
                NORMAL_COLOR = "#64748B"

                if typ in ["top10", "bottom10"]:
                    if len(df.columns) >= 2:
                        st.bar_chart(df.set_index(df.columns[0])[df.columns[1]], use_container_width=True, height=520)

                elif typ == "growth_rate":
                    if "Year" in df.columns:
                        st.line_chart(df.set_index("Year"), use_container_width=True, height=520)
                        st.caption("Each line represents one selected country")
                    else:
                        st.bar_chart(df.set_index(df.columns[0])[df.columns[1]], use_container_width=True, height=520)

                elif typ in ["avg_continent", "total_gdp_continent"]:
                    value_col = "Avg_GDP" if typ == "avg_continent" else "Total_GDP"
                    fig = px.bar(
                        df.sort_values("Continent"),
                        x="Continent",
                        y=value_col,
                        color="is_selected",
                        color_discrete_map={True: SELECTED_COLOR, False: NORMAL_COLOR},
                        title=selected["title"]
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                elif typ == "contribution":
                    df = df.sort_values("Continent").reset_index(drop=True)
                    fig = px.pie(
                        df,
                        values="Contribution_%",
                        names="Continent",
                        color="is_selected",
                        color_discrete_map={True: SELECTED_COLOR, False: NORMAL_COLOR},
                        title=selected["title"],
                        hole=0.3
                    )
                    fig.update_traces(textposition="inside", textinfo="percent+label")
                    st.plotly_chart(fig, use_container_width=True)

                elif typ == "decline":
                    # Multiple separate modern line charts under ONE title
                    if not isinstance(data, list):
                        st.warning("Invalid decline data format.")
                    else:
                        st.markdown("#### Countries with Consistent GDP Decline")
                        for country_entry in data:
                            country = country_entry.get("country", "Unknown")
                            chart_data = country_entry.get("chart_data", [])

                            if not chart_data:
                                continue

                            chart_df = pd.DataFrame(chart_data)

                            if "Year" not in chart_df.columns or "GDP" not in chart_df.columns:
                                st.warning(f"Missing Year/GDP for {country}")
                                continue

                            fig = px.line(
                                chart_df,
                                x="Year",
                                y="GDP",
                                markers=True,
                                title=f"GDP Trend – {country}",
                                color_discrete_sequence=["#EF4444"]
                            )

                            # Modern semi-transparent red gradient fill
                            fig.add_scatter(
                                x=chart_df["Year"],
                                y=chart_df["GDP"],
                                fill="tozeroy",
                                fillcolor="rgba(239, 68, 68, 0.12)",
                                line=dict(color="rgba(0,0,0,0)"),
                                showlegend=False,
                                hoverinfo="skip"
                            )

                            fig.update_traces(
                                line=dict(width=3.5, color="#EF4444"),
                                marker=dict(size=9, color="#EF4444", symbol="circle", line=dict(width=1, color="white"))
                            )

                            fig.update_layout(
                                xaxis_title="Year",
                                yaxis_title="GDP (current US$)",
                                showlegend=False,
                                plot_bgcolor="rgba(0,0,0,0)",
                                paper_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="#e5e7eb"),
                                margin=dict(l=40, r=40, t=60, b=60),
                                height=400
                            )

                            st.plotly_chart(fig, use_container_width=True)
                            st.caption(f"Declining trend for {country} • Red line = actual values • Shaded area = emphasis")
                            st.markdown("---")  # visual separator

                else:
                    st.dataframe(df, use_container_width=True)

            else:
                st.info("No data available for this visualization.")

            st.caption("💡 Hover over charts for details • Scroll / drag to interact")