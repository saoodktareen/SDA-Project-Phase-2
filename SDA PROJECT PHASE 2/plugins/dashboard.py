import streamlit as st
import json
import pandas as pd
import sys
import os

st.set_page_config(page_title="GDP Analysis Dashboard", layout="wide", page_icon="🌍")

st.title("🌍 World GDP Analysis Dashboard – Phase 2")
st.markdown("### All 8 Required Visualizations – Click sidebar to switch")

# Get path from command line
if len(sys.argv) > 1:
    data_path = sys.argv[1]
else:
    st.error("No data file provided.")
    st.stop()

# Load data
try:
    with open(data_path, encoding="utf-8") as f:
        records = json.load(f)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar
st.sidebar.title("📊 Visualizations")
titles = [r.get("title", f"Visualization {i+1}") for i, r in enumerate(records)]
selected_title = st.sidebar.radio("Select:", titles, index=0)

# Show selected
selected = next((r for r in records if r.get("title") == selected_title), None)

if selected:
    st.subheader(selected["title"])
    data = selected.get("data", [])

    if not data:
        st.info("No data available.")
    else:
        df = pd.DataFrame(data)

        if selected["type"] in ["top10", "bottom10", "avg_continent", "contribution", "growth_rate", "fastest_continent"]:
            if len(df.columns) >= 2:
                x = df.columns[0]
                y = df.columns[1]
                st.bar_chart(df.set_index(x)[y], use_container_width=True, height=550)
            else:
                st.dataframe(df, use_container_width=True)

        elif selected["type"] == "global_trend":
            if "Year" in df.columns and "Total_GDP" in df.columns:
                st.line_chart(df.set_index("Year")["Total_GDP"], use_container_width=True, height=550)
            else:
                st.dataframe(df)

        elif selected["type"] == "decline":
            st.dataframe(df, use_container_width=True)

else:
    st.warning("No matching visualization found.")

st.caption("💡 Switch between views using the sidebar · Interactive charts")
