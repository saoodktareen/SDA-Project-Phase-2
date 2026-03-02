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
            print("\n" + "="*80)
            print(r.get("title", "RESULT").center(80))
            print("="*80)
            print(pd.DataFrame(r.get("data", [])).to_string(index=False))
            print()

class GraphicsChartWriter(DataSink):
    def write(self, records: List[dict]) -> None:
        """Save results to temp JSON and launch streamlit_app.py"""
        print("Launching interactive dashboard...")

        # Save results to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as tmp:
            json.dump(records, tmp, indent=2)
            tmp_path = tmp.name

        # Path to your dashboard
        dashboard_path = os.path.join(os.path.dirname(__file__), "..", "streamlit_app.py")

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