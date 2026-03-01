# File: dashboard.py
# Changes: Updated to use Plotly for advanced charts (pie, bar with colors), handle all types from engine.py results, similar to streamlit_app.py display logic. Removed old truncated parts, made it consistent.

import streamlit as st
import json
import pandas as pd
import sys
import plotly.express as px

st.set_page_config(page_title="GDP Analysis Dashboard", layout="wide", page_icon="🌍")

st.title("🌍 World GDP Analysis Dashboard – Phase 2")
st.markdown("### All Required Visualizations – Click sidebar to switch")

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
        typ = selected.get("type", "")
        SELECTED_COLOR = "#F59E0B"  # amber
        NORMAL_COLOR = "#64748B"    # slate

        if typ in ["top10", "bottom10"]:
            if len(df.columns) >= 2:
                st.bar_chart(df.set_index(df.columns[0])[df.columns[1]], use_container_width=True, height=550)

        elif typ == "growth_rate":
            if "Year" in df.columns:
                st.line_chart(df.set_index("Year"), use_container_width=True, height=550)
                st.caption("Each line = one selected country (auto-colored)")
            else:
                st.bar_chart(df.set_index(df.columns[0])[df.columns[1]], use_container_width=True, height=550)

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

        elif typ == "global_trend":
            if "Year" in df.columns and "Total_GDP" in df.columns:
                st.line_chart(df.set_index("Year")["Total_GDP"], use_container_width=True, height=550)
            else:
                st.dataframe(df)

        elif typ == "decline":
            st.dataframe(df, use_container_width=True)

        else:
            st.dataframe(df, use_container_width=True)

else:
    st.warning("No matching visualization found.")

st.caption("💡 Switch between views using the sidebar · Interactive charts")