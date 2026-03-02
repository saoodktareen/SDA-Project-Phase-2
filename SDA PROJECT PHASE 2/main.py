import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from core.contracts import PipelineService, DataSink
from plugins.inputs import CSVReader, JSONReader
from plugins.outputs import ConsoleWriter, GraphicsChartWriter
from core.load_json import load_json
from core.engine import TransformationEngine

INPUT_DRIVERS = {"csv": CSVReader, "json": JSONReader}
OUTPUT_DRIVERS = {"console": ConsoleWriter, "graphics": GraphicsChartWriter}

def bootstrap():
    config = load_json("config.json")
    
    # Get output type from config
    output_type = config.get("output_type", "graphics")  # default to graphics if missing
    
    # Select the correct writer
    sink_cls = OUTPUT_DRIVERS.get(output_type)
    if sink_cls is None:
        print(f"Error: Invalid output_type '{output_type}' in config.json. Must be 'console' or 'graphics'.")
        sys.exit(1)
    
    sink = sink_cls()
    
    # Create engine
    core = TransformationEngine(sink, config["analysis"])
    
    # Select input reader
    input_type = config.get("input_type", "csv")
    input_cls = INPUT_DRIVERS.get(input_type)
    if input_cls is None:
        print(f"Error: Invalid input_type '{input_type}' in config.json. Must be 'csv' or 'json'.")
        sys.exit(1)
    
    reader = input_cls(core, config["data_path"])
    
    # Run the pipeline
    reader.run()

    # For console mode: no further action needed (prints done, exit)
    if output_type == "console":
        print("\nConsole output complete.")
        sys.exit(0)

if __name__ == "__main__":
    bootstrap()