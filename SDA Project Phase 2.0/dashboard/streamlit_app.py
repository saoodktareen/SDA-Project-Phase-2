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
                try:
                    raw_data = json.load(uploaded_raw)
                except json.JSONDecodeError as json_err:
                    st.error(f"Invalid JSON format in raw data file:\n{json_err}\n\n"
                             f"Line: {json_err.lineno}, Column: {json_err.colno}\n"
                             "Please fix the JSON syntax and try again.")
                    st.stop()
                except Exception as e:
                    st.error(f"Failed to read JSON raw data file: {e}")
                    st.stop()

                if not isinstance(raw_data, list):
                    st.error("JSON raw data must be a list of country records (wide format like your attached file).")
                    st.stop()

                try:
                    df_wide = pd.DataFrame(raw_data)
                except Exception as e:
                    st.error(f"Failed to convert JSON to DataFrame: {e}")
                    st.stop()
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

                # ── Otherwise treat as data JSON (but this uploader is only for config) ──
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

    # Prepare countries list
    all_countries = []
    if st.session_state.get("data") is not None:
        try:
            all_countries = sorted(
                st.session_state["data"]["Country Name"].dropna().unique().tolist()
            )
        except KeyError:
            st.warning("Could not find 'Country Name' column in data.")

    # ── Different UI depending on mode ──
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

    # ── Run Analysis button (outside form in upload mode) ──
    if is_upload_mode:
        run_button = st.button("Run Analysis", use_container_width=True, type="primary")
        submitted = run_button
    else:
        # submitted is already set from form
        pass

    # ── Execute when submitted ──
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
            "operation": "sum",  # fixed value
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
                # For decline type, data is list of dicts (not flat DataFrame)
                if typ == "decline":
                    st.markdown("#### GDP Trend – Selected Countries (Last {} Years)".format(selected.get("decline_years_requested", "N/A")))

                    for entry in data:
                        country = entry.get("country", "Unknown")
                        is_decline = entry.get("is_decline", False)
                        years_checked = entry.get("years_checked", 0)
                        start_y = entry.get("start_year")
                        end_y = entry.get("end_year")

                        chart_data = entry.get("chart_data", [])
                        if not chart_data:
                            continue

                        chart_df = pd.DataFrame(chart_data)

                        if "Year" not in chart_df.columns or "GDP" not in chart_df.columns:
                            st.warning(f"Missing data for {country}")
                            continue

                        fig = px.line(
                            chart_df,
                            x="Year",
                            y="GDP",
                            markers=True,
                            title=f"{country} (Checked {years_checked} years: {start_y}–{end_y})",
                            color_discrete_sequence=["#EF4444" if is_decline else "#10B981"]
                        )

                        # Gradient fill: red if decline, green if not
                        fill_color = "rgba(239, 68, 68, 0.15)" if is_decline else "rgba(16, 185, 129, 0.15)"
                        fig.add_scatter(
                            x=chart_df["Year"],
                            y=chart_df["GDP"],
                            fill="tozeroy",
                            fillcolor=fill_color,
                            line=dict(color="rgba(0,0,0,0)"),
                            showlegend=False,
                            hoverinfo="skip"
                        )

                        fig.update_traces(
                            line=dict(width=3),
                            marker=dict(size=8)
                        )

                        fig.update_layout(
                            xaxis_title="Year",
                            yaxis_title="GDP (current US$)",
                            showlegend=False,
                            height=400
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        status = "↓ Consistent Decline" if is_decline else "No consistent decline"
                        st.caption(f"{country}: {status} over checked period")
                        st.markdown("---")

                else:
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
                    
                    elif typ == "fastest_growing_continent":
                        df = pd.DataFrame(data)

                        if df.empty:
                            st.info("No sufficient data to calculate growth rates.")
                        else:
                            continent = df.iloc[0]["Continent"]
                            growth_rate = df.iloc[0]["Growth_Rate_%"]
                            start_gdp = df.iloc[0]["Start_GDP"]
                            end_gdp = df.iloc[0]["End_GDP"]
                            period = df.iloc[0]["Period"]

                            fig = px.bar(
                                df,
                                x="Continent",
                                y="Growth_Rate_%",
                                color="Continent",
                                color_discrete_sequence=["#10B981"],  # green for growth
                                title=selected["title"],
                                text=df["Growth_Rate_%"].apply(lambda x: f"{x}%")
                            )

                            fig.update_traces(
                                textposition="auto",
                                textfont_size=14,
                                marker_line_width=1.5
                            )

                            fig.update_layout(
                                xaxis_title="Fastest Growing Continent",
                                yaxis_title="Average Annual Growth Rate (%)",
                                showlegend=False,
                                height=400
                            )

                            st.plotly_chart(fig, use_container_width=True)

                            st.markdown(f"**{continent}** was the fastest growing continent in {period} with **{growth_rate}%** average annual growth.")
                            st.caption(f"Start GDP: ${start_gdp:,.2f} → End GDP: ${end_gdp:,.2f}")

                    else:
                        st.dataframe(df, use_container_width=True)

            else:
                st.info("No data available for this visualization.")

            st.caption("💡 Hover over charts for details • Scroll / drag to interact")