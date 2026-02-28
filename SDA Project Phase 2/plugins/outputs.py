from typing import List
import os
import tempfile
import json
import subprocess
import sys

class ConsoleWriter:
    def write(self, records: List[dict]) -> None:
        for r in records:
            print("\n" + "="*100)
            print(r.get("title", "RESULT").center(100))
            print("="*100)
            for item in r.get("data", []):
                print(item)
            print()


class GraphicsChartWriter:
    def write(self, records: List[dict]) -> None:
        """Launch interactive Streamlit dashboard with sidebar navigation"""
        print("🚀 Preparing Interactive GDP Dashboard...")

        # Step 1: Save results to a temporary JSON file
        try:
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.json',
                mode='w',
                encoding='utf-8'
            )
            json.dump(records, temp_file, indent=2, ensure_ascii=False)
            temp_file_path = temp_file.name
            temp_file.close()
        except Exception as e:
            print(f"Error saving temporary data: {e}")
            return

        # Step 2: Path to dashboard script (next to this file)
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")

        # Step 3: Create dashboard.py if it doesn't exist
        if not os.path.exists(dashboard_path):
            print("Creating dashboard.py for the first time...")
            try:
                with open(dashboard_path, "w", encoding="utf-8") as f:
                    f.write('''import streamlit as st
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
''')
                print("dashboard.py created successfully.")
            except Exception as e:
                print(f"Error creating dashboard.py: {e}")
                return

        # Step 4: Prepare command with quoted paths
        cmd_list = [
            sys.executable,
            "-m", "streamlit", "run",
            f'"{dashboard_path}"',
            "--",
            f'"{temp_file_path}"'
        ]
        cmd_str = " ".join(cmd_list)

        # Print manual command always (helpful fallback)
        print("\n" + "="*80)
        print("To open the dashboard:")
        print("   " + cmd_str)
        print("Or visit: http://localhost:8501")
        print("Keep this terminal open while viewing.")
        print("="*80)

        # Step 5: Try to launch automatically
        try:
            subprocess.Popen(
                cmd_str,
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            print("Launch attempted — wait 5–10 seconds, then open http://localhost:8501 manually if browser doesn't appear.")
        except Exception as e:
            print(f"Auto-launch failed: {e}")
            print("Please copy and run the command above manually in a new terminal.")