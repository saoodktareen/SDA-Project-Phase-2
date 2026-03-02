from typing import List
import os
import subprocess
import sys
import tempfile
import json
from core.contracts import DataSink
import pandas as pd

# ── Input readers (already there) ────────────────────────────────────────
class CSVReader:
    def __init__(self, service, data_path: str):
        self.service = service
        self.data_path = data_path

    def run(self):
        from core.load_data import load_data
        from core.cleaner import clean_data
        from core.transform import transform_to_long
        df_wide = load_data(self.data_path)
        cleaned_wide, _ = clean_data(df_wide)
        df_long = transform_to_long(cleaned_wide)
        self.service.execute(df_long.to_dict("records"))

class JSONReader:
    def __init__(self, service, data_path: str):
        self.service = service
        self.data_path = data_path

    def run(self):
        from core.cleaner import clean_data
        from core.transform import transform_to_long
        with open(self.data_path) as f:
            data = json.load(f)
        df_wide = pd.DataFrame(data)
        cleaned_wide, _ = clean_data(df_wide)
        df_long = transform_to_long(cleaned_wide)
        self.service.execute(df_long.to_dict("records"))

# ── Output writers (add these back) ──────────────────────────────────────
class ConsoleWriter(DataSink):
    def write(self, records: List[dict]) -> None:
        for r in records:
            title = r.get("title", "RESULT").upper()
            print("\n" + "=" * 100)
            print(title.center(100))
            print("=" * 100)

            typ = r.get("type")
            data = r.get("data", [])

            if typ == "decline":
                if not data:
                    print("No countries showed consistent GDP decline in the selected period.")
                    continue

                print(f"GDP Trend – Last {data[0].get('decline_years_requested', 'N/A')} Years for Selected Countries")
                print("-" * 100)

                # Table header
                header = f"{'Country':<12} {'Decline?':<10} {'Years Checked':<14} {'Period':<15} {'Growth Rate (%)':>15}"
                print(header)
                print("-" * 100)

                for entry in data:
                    country = entry.get("country", "Unknown")
                    is_decline = entry.get("is_decline", False)
                    years_checked = entry.get("years_checked", 0)
                    start_y = entry.get("start_year", "N/A")
                    end_y = entry.get("end_year", "N/A")
                    # Optional: calculate average annual growth rate if needed
                    chart_data = entry.get("chart_data", [])
                    if chart_data:
                        first_gdp = chart_data[0].get("GDP", 0)
                        last_gdp = chart_data[-1].get("GDP", 0)
                        growth_rate = ((last_gdp - first_gdp) / first_gdp * 100) if first_gdp != 0 else 0
                        growth_str = f"{growth_rate:.2f}%"
                    else:
                        growth_str = "N/A"

                    status = "YES ↓" if is_decline else "NO"
                    line = f"{country:<12} {status:<10} {years_checked:<14} {start_y}–{end_y:<15} {growth_str:>15}"
                    print(line)

                print("-" * 100)
                print("Note: 'YES ↓' = Strict consecutive GDP decline over checked period")

            elif typ in ["top10", "bottom10"]:
                print(pd.DataFrame(data).to_string(index=False))

            elif typ == "growth_rate":
                df = pd.DataFrame(data)
                print(df.to_string(index=False))

            elif typ in ["avg_continent", "total_gdp_continent"]:
                df = pd.DataFrame(data)
                print(df.to_string(index=False))

            elif typ == "contribution":
                df = pd.DataFrame(data)
                print(df.to_string(index=False))

            elif typ == "fastest_growing_continent":
                df = pd.DataFrame(data)
                print(df.to_string(index=False))

            else:
                print(pd.DataFrame(data).to_string(index=False))

            print("\n")

class GraphicsChartWriter(DataSink):
    def write(self, records: List[dict]) -> None:
        """Save results to temp JSON and launch streamlit_app.py"""
        print("Launching interactive dashboard...")

        # Save results to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as tmp:
            json.dump(records, tmp, indent=2)
            tmp_path = tmp.name

        # Path to your dashboard
        dashboard_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard", "streamlit_app.py"))

        # Launch Streamlit with the temp file as argument
        cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path, "--", tmp_path]
        try:
            subprocess.Popen(cmd)
            print(f"Dashboard launched! Open http://localhost:8501 (or wait a few seconds)")
            print(f"Temp data saved to: {tmp_path} (you can delete it later)")
        except Exception as e:
            print(f"Failed to launch: {e}")
            print("Run manually:")
            print(" ".join(cmd))