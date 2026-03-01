from typing import List
import os
import json
import subprocess
import webbrowser
import time
import platform
import sys

class ConsoleWriter:
    def write(self, records: List[dict]) -> None:
        """
        Prints results to console in a formatted way (Phase 1 style).
        Uses functional style with map/lambda.
        """
        list(map(
            lambda r: print(
                "\n" + "=" * 100 + "\n" +
                r.get("title", "RESULT").center(100) + "\n" +
                "=" * 100 + "\n" +
                "\n".join(map(str, r.get("data", []))) + "\n"
            ),
            records
        ))

class StreamlitSink:
    def write(self, records: List[dict]) -> None:
        """
        Writes records to temp JSON for Streamlit to load, then launches.
        """
        print("[StreamlitSink] Received records → saving to temp and launching...")

        # Save to temp file
        temp_path = "temp_records.json"
        with open(temp_path, "w") as f:
            json.dump(records, f)

        # Launch Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.headless=true"
        ]

        creationflags = 0
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

        try:
            proc = subprocess.Popen(
                cmd,
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            print(f"[StreamlitSink] Streamlit process started (PID: {proc.pid})")
            time.sleep(6)  # Give more time for server to be ready
            webbrowser.open("http://localhost:8501")
        except Exception as e:
            print(f"[StreamlitSink] Failed to launch Streamlit: {e}")
            # Fallback: print records to console
            print("\n[StreamlitSink FALLBACK] Could not launch dashboard. Records:")
            ConsoleWriter().write(records)