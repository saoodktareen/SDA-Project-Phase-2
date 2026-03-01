# Make the project folder behave like a proper package (fixes import errors)
# Force UTF-8 encoding for stdout/stderr (Windows fix)
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import subprocess
import webbrowser
import time
import os
import platform

from core.contracts import PipelineService, DataSink
from plugins.inputs import CSVReader, JSONReader, ExcelReader, BrowserReader  # ← added BrowserReader
from plugins.outputs import ConsoleWriter, StreamlitSink
from core.load_config import load_config
from core.engine import TransformationEngine
from core.validate_json import validate_json

# Updated drivers – added browser
INPUT_DRIVERS = {
    "csv": CSVReader,
    "json": JSONReader,
    "excel": ExcelReader,
    "browser": BrowserReader,
}

OUTPUT_DRIVERS = {
    "console": ConsoleWriter,
    "graphics": StreamlitSink,
    "streamlit": StreamlitSink,
    "dashboard": StreamlitSink,   # Phase 1 compatibility
}

def bootstrap():
    print("[MAIN] Starting bootstrap process...")

    # Handle config source (file or browser)
    config_path = "config.json"  # Default
    config_source = "file"  # Default
    if os.path.exists(config_path):
        raw_config = load_config(config_path)
        config_source = raw_config.get("config_source", "file")
        if config_source == "browser":
            config_url = raw_config.get("config_url")
            if config_url:
                print(f"[MAIN] Fetching config from browser URL: {config_url}")
                raw_config = load_config(config_url)  # load_config handles http

    # 1. Load raw config
    raw_config = load_config(config_path)

    # 2. Validate config
    validated_config, errors = validate_json(raw_config)
    if errors:
        # Handle errors with dummy sink
        sink = ConsoleWriter() if raw_config.get("output_type", "console") == "console" else StreamlitSink()
        sink.write([{"type": "errors", "title": "Validation Errors", "data": errors}])
        return

    # Set env for Streamlit if needed
    os.environ["SDA_CONFIG_PATH"] = config_path
    os.environ["SDA_VALIDATED_CONFIG"] = str(validated_config)
    os.environ["SDA_ERRORS"] = str(errors)

    # 3. Instantiate Output (the Sink)
    output_type = validated_config.get("output_type", "console")
    sink_class = OUTPUT_DRIVERS.get(output_type)
    if not sink_class:
        raise ValueError(f"Invalid output_type: {output_type}")
    sink = sink_class()

    # 4. Instantiate Core (inject the Sink)
    core = TransformationEngine(sink, validated_config)

    # 5. Instantiate Input (inject the Core)
    input_type = validated_config.get("input_type")
    data_path = validated_config.get("data_path")
    input_class = INPUT_DRIVERS.get(input_type)
    if not input_class:
        raise ValueError(f"Invalid input_type: {input_type}")
    reader = input_class(core, data_path)

    # 6. Run the Input
    if output_type in {"streamlit", "dashboard", "graphics"}:
        # Launch Streamlit via subprocess
        print("[MAIN] Launching Streamlit dashboard...")
        cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless=true"]

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
            print(f"[MAIN] Streamlit launched (PID: {proc.pid})")
            time.sleep(5)  # give it time to start
            webbrowser.open("http://localhost:8501")
        except Exception as e:
            print(f"[MAIN] Failed to launch Streamlit: {e}")
            sink.write([{"type": "errors", "title": "Streamlit Launch Failed", "data": [str(e)]}])
    else:
        # Console mode – run directly
        reader.run()
        print("[MAIN] Console analysis complete.")

if __name__ == "__main__":
    bootstrap()