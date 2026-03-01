# File: plugins/outputs.py
# Changes: Changed dashboard_path to "streamlit_app.py" since streamlit_app.py now handles both interactive and viewer modes (with sys.argv check). Added os.path.abspath to resolve relative paths properly, preventing issues with '..' in Windows. This should fix the "File does not exist" error by providing a fully resolved absolute path to Streamlit.

from typing import List
import os
import subprocess
import sys
import tempfile
import json
from core.contracts import DataSink
import pandas as pd

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

        # Path to your dashboard - use abspath to resolve fully
        dashboard_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "streamlit_app.py"))

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