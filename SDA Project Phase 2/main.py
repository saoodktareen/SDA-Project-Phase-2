# Make the project folder behave like a proper package (fixes import errors)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

# Now the normal imports work
from core.contracts import PipelineService, DataSink
from plugins.inputs import CSVReader, JSONReader
from plugins.outputs import ConsoleWriter, GraphicsChartWriter
from core.load_json import load_json
from core.engine import TransformationEngine

INPUT_DRIVERS = {"csv": CSVReader, "json": JSONReader}
OUTPUT_DRIVERS = {"console": ConsoleWriter, "graphics": GraphicsChartWriter}

def bootstrap():
    config = load_json("config.json")
    
    # Create concrete Sink using factory
    sink_cls = OUTPUT_DRIVERS[config["output_type"]]
    sink: DataSink = sink_cls()
    
    # Create Core Engine → Dependency Injection of sink
    core = TransformationEngine(sink, config["analysis"])
    
    # Create Input reader → Dependency Injection of core (as PipelineService)
    input_cls = INPUT_DRIVERS[config["input_type"]]
    reader = input_cls(core, config["data_path"])
    
    # Start data flow
    reader.run()

if __name__ == "__main__":
    bootstrap()