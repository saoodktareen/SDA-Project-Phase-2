# Force UTF-8 encoding for stdout/stderr (Windows fix)
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

import streamlit as st
import pandas as pd
import json
import os
import ast
from pathlib import Path
from typing import List, Dict, Any
import io  # for reading uploaded files
import altair as alt

# Import core logic for "Run" processing
from core.load_config import load_config
from core.validate_json import validate_json
from core.engine import TransformationEngine
from core.contracts import DataSink
from plugins.inputs import CSVReader, JSONReader, ExcelReader, BrowserReader
from core.visualize_errors import visualize_errors
from core.visualize_countries import get_country_charts
from core.visualize_regions import get_region_charts

# ────────────────────────────────────────────────
# Page config & styling
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="GDP Analysis Dashboard – SDA Phase 2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {background-color: #0e1117;}
    h1, h2, h3 {color: #3B82F6 !important;}
    .stSidebar {background-color: #161b22;}
    .stRadio > div {background-color: #1f2937; padding: 10px; border-radius: 5px;}
    .stButton > button {background-color: #3B82F6; color: white;}
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Session State Setup
# ────────────────────────────────────────────────
if "has_data" not in st.session_state:
    st.session_state.has_data = False
if "records" not in st.session_state:
    st.session_state.records = []
if "errors" not in st.session_state:
    st.session_state.errors = []
if "validated_config" not in st.session_state:
    st.session_state.validated_config = {}

# Try to load from temp file (from sink)
temp_path = "temp_records.json"
if os.path.exists(temp_path):
    with open(temp_path, "r") as f:
        records = json.load(f)
    st.session_state.records = records
    st.session_state.has_data = True
    os.remove(temp_path)  # Clean up

# Load config from env or file
config_path = os.environ.get("SDA_CONFIG_PATH", "config.json")
raw_config = load_config(config_path)
validated_config, errors = validate_json(raw_config)
st.session_state.validated_config = validated_config
st.session_state.errors = errors or ast.literal_eval(os.environ.get("SDA_ERRORS", "[]"))

# ────────────────────────────────────────────────
# Sidebar
# ────────────────────────────────────────────────
st.sidebar.title("GDP Dashboard")
page = st.sidebar.radio(
    "Sections",
    ["Home", "Errors", "Countries", "Regions", "Top/Bottom", "Growth", "Trends", "Raw Data"]
)

# Uploaders
uploaded_config = st.sidebar.file_uploader("Upload Config (JSON/CSV)", type=["json", "csv"])
uploaded_data = st.sidebar.file_uploader("Upload Data (CSV/JSON/Excel)", type=["csv", "json", "xlsx"])

# Run button
if st.sidebar.button("Run Analysis"):
    if uploaded_config:
        config_content = uploaded_config.read().decode()
        if uploaded_config.type == "application/json":
            raw_config = json.loads(config_content)
        else:  # CSV
            df = pd.read_csv(io.StringIO(config_content))
            raw_config = df.set_index('key')['value'].to_dict()
        validated_config, errors = validate_json(raw_config)
        st.session_state.validated_config = validated_config
        st.session_state.errors = errors

    input_type = validated_config.get("input_type", "csv")
    data_path = uploaded_data.name if uploaded_data else validated_config.get("data_path")

    # Temp save uploaded data
    if uploaded_data:
        with open(data_path, "wb") as f:
            f.write(uploaded_data.getvalue())

    # Run input -> core -> sink (dummy sink for Streamlit)
    class DummySink(DataSink):
        def write(self, records: List[dict]):
            with open("temp_records.json", "w") as f:
                json.dump(records, f)

    core = TransformationEngine(DummySink(), validated_config)
    input_class = {"csv": CSVReader, "json": JSONReader, "excel": ExcelReader, "browser": BrowserReader}.get(input_type)
    reader = input_class(core, data_path)
    reader.run()
    st.session_state.has_data = True
    st.rerun()  # Refresh to load temp

# ────────────────────────────────────────────────
# Main Pages
# ────────────────────────────────────────────────
if page == "Home":
    st.header("Welcome to GDP Analysis Dashboard")
    st.write("Upload config/data and run analysis.")
    if st.session_state.has_data:
        st.success("Data loaded — navigate to sections")
    else:
        st.warning("No data loaded — check Errors")

elif page == "Errors":
    st.header("Errors & Validation Report")
    if st.session_state.errors:
        st.error("Errors found during validation or processing:")
        visualize_errors(csv_errors={}, json_errors=st.session_state.errors)
    else:
        st.success("No errors detected")

elif page == "Countries":
    st.header("Countries Analysis")
    if st.session_state.has_data:
        df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'country_agg' for r in rec['data']])
        charts = get_country_charts(df, st.session_state.validated_config)
        for name, func in charts.items():
            st.subheader(name)
            st.altair_chart(func(), use_container_width=True)
    else:
        st.warning("🔒 This section is locked")

elif page == "Regions":
    st.header("Regions Analysis")
    if st.session_state.has_data:
        df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'region_agg' for r in rec['data']])
        charts = get_region_charts(df, st.session_state.validated_config)
        for name, func in charts.items():
            st.subheader(name)
            st.altair_chart(func(), use_container_width=True)
    else:
        st.warning("🔒 This section is locked")

elif page == "Top/Bottom":
    st.header("Top/Bottom 10 Countries")
    if st.session_state.has_data:
        top_df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'top10' for r in rec['data']])
        bottom_df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'bottom10' for r in rec['data']])
        st.subheader("Top 10")
        st.dataframe(top_df)
        st.subheader("Bottom 10")
        st.dataframe(bottom_df)
        # Add chart: bar for top/bottom
        if not top_df.empty:
            chart = alt.Chart(top_df).mark_bar().encode(x='Country Name', y='GDP', color='Continent')
            st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("🔒 This section is locked")

elif page == "Growth":
    st.header("Growth Rates & Declines")
    if st.session_state.has_data:
        growth_df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'growth_rates' for r in rec['data']])
        declines_df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'declines' for r in rec['data']])
        fastest_df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'fastest_growing' for r in rec['data']])
        st.subheader("Growth Rates")
        st.dataframe(growth_df)
        st.subheader("Declining Countries")
        st.dataframe(declines_df)
        st.subheader("Fastest Growing Continents")
        st.dataframe(fastest_df)
        # Add line chart for growth
        if not growth_df.empty:
            chart = alt.Chart(growth_df).mark_line().encode(x='Year', y='Growth Rate', color='Continent')
            st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("🔒 This section is locked")

elif page == "Trends":
    st.header("Trends & Contributions")
    if st.session_state.has_data:
        trends_df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'trends' for r in rec['data']])
        contrib_df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'contributions' for r in rec['data']])
        avgs_df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'averages' for r in rec['data']])
        st.subheader("Yearly Trends")
        st.dataframe(trends_df)
        st.subheader("Continent Contributions")
        st.dataframe(contrib_df)
        st.subheader("Averages per Continent/Year")
        st.dataframe(avgs_df)
        # Add area chart for trends
        if not trends_df.empty:
            chart = alt.Chart(trends_df).mark_area().encode(x='Year', y='GDP', color='Continent')
            st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("🔒 This section is locked")

elif page == "Raw Data":
    st.header("Raw Data Preview")
    if st.session_state.has_data and st.session_state.records:
        df = pd.DataFrame([r for rec in st.session_state.records if rec['type'] == 'raw_preview' for r in rec['data']])
        st.dataframe(df, use_container_width=True)
        st.caption(f"Showing first 200 rows")
    else:
        st.warning("No data loaded")

# Footer
st.markdown("---")
st.caption("SDA Project Phase 2 • Shaheer Saikhani & Saood Khan Tareen • BCS-4A")