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
    sink_cls = OUTPUT_DRIVERS[config["output_type"]]
    sink = sink_cls()
    
    core = TransformationEngine(sink, config["analysis"])
    
    input_cls = INPUT_DRIVERS[config["input_type"]]
    reader = input_cls(core, config["data_path"])
    
    reader.run()

if __name__ == "__main__":
    bootstrap()