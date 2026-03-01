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

for key, default in [
    ("step", "input"),
    ("results", []),
    ("data", None),
    ("raw_data_wide", None),
    ("raw_errors", {}),
    ("config", {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# INPUT PAGE
if st.session_state["step"] == "input":
    st.title("🌍 World GDP Analysis Dashboard")
    st.markdown("Upload data and configure your analysis")

    tab1, tab2, tab3 = st.tabs(["Upload CSV", "Upload JSON", "Use Default"])

    df_wide = None
    errors = {}

    with tab1:
        uploaded = st.file_uploader("Upload CSV file", type="csv", key="csv_upload")
        if uploaded:
            try:
                df_wide = pd.read_csv(uploaded)
                df_wide, errors = clean_data(df_wide)
                st.success(f"Loaded & cleaned: {len(df_wide)} rows")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab2:
        uploaded = st.file_uploader("Upload JSON file", type="json", key="json_upload")
        if uploaded:
            try:
                data = json.load(uploaded)
                df_wide = pd.DataFrame(data)
                df_wide, errors = clean_data(df_wide)
                st.success(f"Loaded & cleaned: {len(df_wide)} rows")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab3:
        if st.button("Load default (gdp_with_continent_filled.csv)"):
            try:
                from core.load_data import load_data
                df_raw = load_data("data/gdp_with_continent_filled.csv")
                df_wide, errors = clean_data(df_raw)
                st.success(f"Default loaded: {len(df_wide)} rows")
            except Exception as e:
                st.error(f"Error: {e}")

    if df_wide is not None:
        st.divider()
        st.subheader("Data Quality Summary")
        if any(len(v) > 0 for v in errors.values()):
            for k, v in errors.items():
                if v:
                    st.warning(f"{k.replace('_',' ').title()}: {len(v)} issues")
        else:
            st.success("Data looks clean ✓")

        st.session_state["raw_data_wide"] = df_wide
        if len(df_wide) > 0:
            df_long = transform_to_long(df_wide)
            st.session_state["data"] = df_long
            st.session_state["raw_errors"] = errors

    st.divider()
    st.subheader("Analysis Settings")

    all_countries = []
    if st.session_state.get("raw_data_wide") is not None:
        all_countries = sorted(st.session_state["raw_data_wide"]["Country Name"].dropna().unique().tolist())

    with st.form(key="analysis_form"):
        col1, col2 = st.columns(2)
        with col1:
            regions = st.multiselect(
                "Regions / Continents",
                options=["Asia", "Europe", "Africa", "North America", "South America", "Oceania", "Global"],
                default=["Europe"]
            )

            selected_countries = st.multiselect(
                "Countries (optional – shows growth rate)",
                options=all_countries,
                default=[]
            )

            target_year = st.number_input("Single Target Year (for Top/Bottom 10)", 1960, 2024, 2020)

        with col2:
            operation = st.selectbox("Aggregation", ["average", "sum"])
            start_year = st.number_input("Start Year", 1960, 2024, 2015)
            end_year = st.number_input("End Year", 1960, 2024, 2020)

        submitted = st.form_submit_button("Run Analysis", use_container_width=True)

    if submitted:
        if st.session_state.get("data") is None:
            st.error("No data loaded yet. Upload a file or use default.")
            st.stop()

        has_loaded_data = st.session_state.get("raw_data_wide") is not None

        if not has_loaded_data and not regions and not selected_countries:
            st.error("Please select at least one region or country (or load a file first).")
            st.stop()

        config = {
            "region": regions if regions else None,
            "country": selected_countries if selected_countries else None,
            "year": int(target_year),
            "start_year": int(start_year),
            "end_year": int(end_year),
            "operation": operation,
        }
        st.session_state["config"] = config

        df = st.session_state["data"].copy()
        df["Year"] = df["Year"].astype(int)

        df_filtered = df.copy()

        if config["region"]:
            df_filtered = df_filtered[df_filtered["Continent"].isin(config["region"])]

        if config["country"]:
            df_filtered = df_filtered[df_filtered["Country Name"].isin(config["country"])]

        has_countries = bool(config["country"])
        if not has_countries:
            if config["year"]:
                df_filtered = df_filtered[df_filtered["Year"] == config["year"]]
            elif config["start_year"] and config["end_year"]:
                df_filtered = df_filtered[
                    (df_filtered["Year"] >= config["start_year"]) &
                    (df_filtered["Year"] <= config["end_year"])
                ]

        df_filtered = df_filtered.dropna(subset=["GDP"])

        if df_filtered.empty and (config["region"] or config["country"]):
            st.error("No data remains after manual filtering. Clear selections to analyze full file.")
        else:
            sink = StreamlitSink()
            engine = TransformationEngine(sink, config)
            engine.execute(df.to_dict("records"))

            st.session_state["step"] = "dashboard"
            st.rerun()

# ────────────────────────────────────────────────────────────────────────────
# DASHBOARD PAGE
# ────────────────────────────────────────────────────────────────────────────
else:
    st.title("🌍 GDP Analysis Dashboard")
    st.markdown("Select a visualization from the sidebar")

    with st.sidebar:
        st.subheader("Views")
        results = st.session_state.get("results", [])
        titles = [r.get("title", f"View {i+1}") for i, r in enumerate(results)]
        selected_title = st.radio("Select:", titles if titles else ["No results"])

        if st.button("← Back to Input"):
            st.session_state["step"] = "input"
            st.rerun()

    if not results:
        st.info("Run an analysis first.")
    else:
        selected = next((r for r in results if r.get("title") == selected_title), None)
        if not selected:
            st.error("View not found.")
        else:
            st.subheader(selected.get("title", "Result"))
            data = selected.get("data", [])
            typ = selected.get("type", "")

            if not data:
                st.info("No data for this view.")
            else:
                df = pd.DataFrame(data)

                with st.expander("Raw Data", expanded=False):
                    st.dataframe(df, use_container_width=True)

                SELECTED_COLOR = "#F59E0B"  # amber
                NORMAL_COLOR = "#64748B"    # slate

                if typ in ["top10", "bottom10"]:
                    if len(df.columns) >= 2:
                        st.bar_chart(df.set_index(df.columns[0])[df.columns[1]], use_container_width=True, height=520)

                elif typ == "growth_rate":
                    if "Year" in df.columns:
                        st.line_chart(df.set_index("Year"), use_container_width=True, height=520)
                        st.caption("Each line = one selected country (auto-colored)")
                    else:
                        st.bar_chart(df.set_index(df.columns[0])[df.columns[1]], use_container_width=True, height=520)

                elif typ in ["avg_continent", "total_gdp_continent"]:
                    value_col = "Avg_GDP" if typ == "avg_continent" else "Total_GDP"
                    colors = df["is_selected"].map({True: SELECTED_COLOR, False: NORMAL_COLOR}).tolist()
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
                    st.caption(f"**Color key**: {SELECTED_COLOR} = Selected Region | {NORMAL_COLOR} = Other")

                elif typ == "contribution":
                    # Fixed highlighting
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
                    st.caption(f"**Color key**: {SELECTED_COLOR} = Selected Region | {NORMAL_COLOR} = Other")

                else:
                    st.dataframe(df, use_container_width=True)

            st.caption("💡 Hover for values • Scroll to zoom • Drag to pan")