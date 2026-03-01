# File: streamlit_app.py
# Changes: Completely revamped the UI to remove tabs, add single upload for CSV/JSON, add Configuration Mode (Automatic/Manual), integrate validation, process data internally, handle output_type ("graphics" shows charts, "console" captures print output in st.code). Added dashboard mode if run with sys.argv[1] (temp.json path). Used TempSink to capture results before writing to actual sink. Integrated cleaner, transform, engine. Show errors in expanders/warnings.

import streamlit as st
import pandas as pd
import json
import sys
import os
import io
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import TransformationEngine
from core.cleaner import clean_data
from core.transform import transform_to_long
from core.contracts import DataSink
from core.validate_json import validate_json  # Updated to new validation logic
from plugins.outputs import ConsoleWriter

class TempSink(DataSink):
    def __init__(self):
        self.records = None

    def write(self, records: list[dict]) -> None:
        self.records = records

class StreamlitSink(DataSink):
    def write(self, records: list[dict]) -> None:
        st.session_state["results"] = records

# Dashboard mode if launched with arg (e.g., from GraphicsChartWriter)
if len(sys.argv) > 1:
    data_path = sys.argv[1]
    try:
        with open(data_path, encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    st.set_page_config(page_title="GDP Analysis Dashboard", layout="wide", page_icon="🌍")
    st.title("🌍 World GDP Analysis Dashboard")
    st.sidebar.title("📊 Visualizations")
    titles = [r.get("title", f"Visualization {i+1}") for i, r in enumerate(records)]
    selected_title = st.sidebar.radio("Select:", titles, index=0)
    selected = next((r for r in records if r.get("title") == selected_title), None)

    if selected:
        st.subheader(selected["title"])
        data = selected.get("data", [])
        if not data:
            st.info("No data available.")
        else:
            df = pd.DataFrame(data)
            typ = selected.get("type", "")
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
else:
    # Interactive mode (no arg provided) - Modified: Removed config_mode radio and uploaded_json. Always use manual inputs for config, keep only CSV upload (default upload).
    st.set_page_config(page_title="World GDP Analyzer", layout="wide", page_icon="📈")
    st.title("🌍 World GDP Analyzer")

    with st.sidebar:
        st.title("⚙️ Settings")
        output_type_val = st.selectbox("Output Type", ["graphics", "console"])

    # Default upload: CSV only
    uploaded_csv = st.file_uploader("Upload CSV Data File", type="csv")

    # Manual config inputs (always shown, no Automatic mode)
    region_input = st.text_input("Region (comma-separated for multiple, leave empty for all)", "")
    country_input = st.text_input("Country (comma-separated for multiple, leave empty for all)", "")
    year_input = st.number_input("Year (optional)", min_value=1960, max_value=2024, value=None, step=1)
    start_year = st.number_input("Start Year", min_value=1960, max_value=2024, value=2015)
    end_year = st.number_input("End Year", min_value=1960, max_value=2024, value=2020)
    operation = st.selectbox("Operation", ["sum", "average"])

    if st.button("Analyze") and uploaded_csv:
        try:
            # Load CSV
            df_wide = pd.read_csv(uploaded_csv)
            cleaned_wide, csv_errors = clean_data(df_wide)
            df_long = transform_to_long(cleaned_wide)

            # Construct config from manual inputs
            config = {
                "region": [r.strip() for r in region_input.split(",") if r.strip()] if region_input else [],
                "country": [c.strip() for c in country_input.split(",") if c.strip()] if country_input else [],
                "start_year": start_year,
                "end_year": end_year,
                "operation": operation
            }
            if year_input:
                config["year"] = year_input

            # Validate config
            clean_df = cleaned_wide  # For validation against uniques
            validated_config, json_errors = validate_json(config, clean_df)

            if json_errors:
                with st.expander("🚨 JSON Config Errors", expanded=True):
                    for err in json_errors:
                        st.error(err)
                st.stop()

            if csv_errors:
                error_msg = ""
                for k, v in csv_errors.items():
                    if v:
                        error_msg += f"{k.replace('_', ' ').title()}: {v}\n"
                if error_msg:
                    with st.expander("⚠️ CSV Data Warnings", expanded=True):
                        st.warning(error_msg)

            # Process
            temp_sink = TempSink()
            engine = TransformationEngine(temp_sink, validated_config)
            engine.execute(df_long.to_dict("records"))

            records = temp_sink.records

            if output_type_val == "graphics":
                st.session_state["results"] = records
                if "results" in st.session_state:
                    records = st.session_state["results"]
                    st.markdown("### 📊 Analysis Results")
                    for selected in records:
                        title = selected.get("title", "Result")
                        typ = selected.get("type", "")
                        df = pd.DataFrame(selected.get("data", []))
                        st.markdown(f"### {title}")
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
                            colors = df["is_selected"].map({True: "#F59E0B", False: "#64748B"}).tolist()
                            fig = px.bar(
                                df.sort_values("Continent"),
                                x="Continent",
                                y=value_col,
                                color="is_selected",
                                color_discrete_map={True: "#F59E0B", False: "#64748B"},
                                title=title
                            )
                            fig.update_layout(showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                            st.caption(f"**Color key**: #F59E0B = Selected Region | #64748B = Other")
                        elif typ == "contribution":
                            df = df.sort_values("Continent").reset_index(drop=True)
                            fig = px.pie(
                                df,
                                values="Contribution_%",
                                names="Continent",
                                color="is_selected",
                                color_discrete_map={True: "#F59E0B", False: "#64748B"},
                                title=title,
                                hole=0.3
                            )
                            fig.update_traces(textposition="inside", textinfo="percent+label")
                            st.plotly_chart(fig, use_container_width=True)
                            st.caption(f"**Color key**: #F59E0B = Selected Region | #64748B = Other")
                        else:
                            st.dataframe(df, use_container_width=True)
                        st.caption("💡 Hover for values • Scroll to zoom • Drag to pan")
            elif output_type_val == "console":
                old_stdout = sys.stdout
                buf = io.StringIO()
                sys.stdout = buf
                console_sink = ConsoleWriter()
                console_sink.write(records)
                sys.stdout = old_stdout
                output = buf.getvalue()
                st.subheader("Console Output")
                st.code(output, language="text")
        except Exception as e:
            st.error(f"Processing error: {str(e)}")
    elif not uploaded_csv:
        st.info("Please upload a CSV file to begin.")