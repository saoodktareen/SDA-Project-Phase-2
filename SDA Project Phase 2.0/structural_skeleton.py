"""
============================================================
  GDP Analysis System — Structural Skeleton
  Generated from PlantUML architecture (architecture.puml)
  Deliverable 13: Structural Python code from PlantUML design
============================================================

This file contains the structural (skeleton) classes that
mirror the PlantUML class diagram exactly.  Every class,
method signature, protocol, and relationship is represented.
The actual business logic lives in the individual module files.
"""

# ─────────────────────────────────────────────────────────────
#  core/contracts.py  — Protocols (owned by Core)
# ─────────────────────────────────────────────────────────────
from typing import Protocol, List, Any, runtime_checkable


@runtime_checkable
class DataSink(Protocol):
    """
    Outbound Abstraction.
    Any Output plugin must implement this exact signature.
    The Core calls this to deliver results — it never knows
    which concrete writer is on the other end.
    """
    def write(self, records: List[dict]) -> None: ...


@runtime_checkable
class PipelineService(Protocol):
    """
    Inbound Abstraction.
    Any Input plugin calls this to push raw data into the Core.
    The Input module never imports a concrete Core class.
    """
    def execute(self, raw_data: List[Any]) -> None: ...


# ─────────────────────────────────────────────────────────────
#  core/engine.py  — TransformationEngine
# ─────────────────────────────────────────────────────────────
import pandas as pd


class TransformationEngine:
    """
    Implements PipelineService (structural, via duck-typing).
    Depends on DataSink (injected at construction — never imported directly).

    Relationship to diagram:
        TransformationEngine ..|> PipelineService  (implements)
        TransformationEngine o--> DataSink          (injected dependency)
    """

    def __init__(self, sink: DataSink, config: dict) -> None:
        self.sink   = sink    # DataSink injected — no concrete import
        self.config = config

    def execute(self, raw_data: List[Any]) -> None:
        """Entry point called by Input plugins via PipelineService protocol."""
        ...

    # ── private analysis methods (8 required outputs) ────────────────────
    @staticmethod
    def _continent_filter(df: pd.DataFrame, region) -> pd.DataFrame: ...

    @staticmethod
    def _country_filter(df: pd.DataFrame, country) -> pd.DataFrame: ...

    def _top10(self, df: pd.DataFrame, region, year: int) -> dict: ...
    def _bottom10(self, df: pd.DataFrame, region, year: int) -> dict: ...
    def _growth_rate(self, df: pd.DataFrame, region, start: int, end: int) -> dict: ...
    def _avg_by_continent(self, df: pd.DataFrame, start: int, end: int) -> dict: ...
    def _global_trend(self, df: pd.DataFrame, start: int, end: int) -> dict: ...
    def _fastest_continent(self, df: pd.DataFrame, start: int, end: int) -> dict: ...
    def _decline_countries(self, df: pd.DataFrame, n_years: int, end: int) -> dict: ...
    def _contribution(self, df: pd.DataFrame, start: int, end: int) -> dict: ...


# ─────────────────────────────────────────────────────────────
#  core/cleaner.py
# ─────────────────────────────────────────────────────────────
class DataCleaner:
    """
    Pure domain logic — no I/O, no framework imports.
    Validates and sanitises a raw wide-format DataFrame.
    """
    def clean_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]: ...


# ─────────────────────────────────────────────────────────────
#  core/transform.py
# ─────────────────────────────────────────────────────────────
class DataTransformer:
    """Converts wide GDP data to tidy long format."""
    def transform_to_long(self, df: pd.DataFrame) -> pd.DataFrame: ...


# ─────────────────────────────────────────────────────────────
#  core/load_data.py  /  core/load_json.py
# ─────────────────────────────────────────────────────────────
class DataLoader:
    """File-system utilities used by Bootstrap and Input plugins."""
    def load_data(self, path: str) -> pd.DataFrame: ...
    def load_json(self, path: str) -> dict: ...


# ─────────────────────────────────────────────────────────────
#  core/process.py
# ─────────────────────────────────────────────────────────────
class ProcessAggregator:
    """Groups and aggregates GDP data by a chosen dimension."""
    def process(self, df: pd.DataFrame, config: dict,
                group_by: str) -> pd.DataFrame: ...


# ─────────────────────────────────────────────────────────────
#  core/filter_by_region.py
# ─────────────────────────────────────────────────────────────
class FilterByRegion:
    """Filters DataFrame rows by continent(s) from config."""
    def filter_by_region(self, df: pd.DataFrame, config: dict) -> pd.DataFrame: ...


# ─────────────────────────────────────────────────────────────
#  core/filter_by_country.py
# ─────────────────────────────────────────────────────────────
class FilterByCountry:
    """Filters DataFrame rows by country name(s) from config."""
    def filter_by_country(self, df: pd.DataFrame, config: dict) -> pd.DataFrame: ...


# ─────────────────────────────────────────────────────────────
#  plugins/inputs.py  — Source plugins
# ─────────────────────────────────────────────────────────────
class CSVReader:
    """
    Reads a CSV file, cleans + transforms it, then hands data
    to the Core via the PipelineService protocol.

    Relationship to diagram:
        CSVReader o--> PipelineService  (injected)
        CSVReader does NOT import TransformationEngine directly
    """
    def __init__(self, service: PipelineService, data_path: str) -> None:
        self.service   = service    # PipelineService — never a concrete class
        self.data_path = data_path

    def run(self) -> None: ...


class JSONReader:
    """
    Reads a JSON file, cleans + transforms it, then hands data
    to the Core via the PipelineService protocol.
    """
    def __init__(self, service: PipelineService, data_path: str) -> None:
        self.service   = service
        self.data_path = data_path

    def run(self) -> None: ...


# ─────────────────────────────────────────────────────────────
#  plugins/outputs.py  — Sink plugins
# ─────────────────────────────────────────────────────────────
class ConsoleWriter:
    """
    Satisfies DataSink.  Writes results to stdout.

    Relationship to diagram:
        ConsoleWriter ..|> DataSink  (implements — structurally, via duck-typing)
    """
    def write(self, records: List[dict]) -> None: ...


class GraphicsChartWriter:
    """
    Satisfies DataSink.  Serialises results and launches Streamlit dashboard.
    """
    def write(self, records: List[dict]) -> None: ...


class StreamlitSink:
    """
    Satisfies DataSink.  Used inside streamlit_app.py.
    Stores results in st.session_state for the UI to render.
    """
    def write(self, records: List[dict]) -> None: ...


# ─────────────────────────────────────────────────────────────
#  main.py  — Bootstrap / Orchestrator
# ─────────────────────────────────────────────────────────────

# Registry-based Factory (dictionary maps config strings → classes)
INPUT_DRIVERS: dict  = {"csv": CSVReader,  "json": JSONReader}
OUTPUT_DRIVERS: dict = {"console": ConsoleWriter, "graphics": GraphicsChartWriter}


class Bootstrap:
    """
    The General Contractor.
    Reads config.json, wires all components via Dependency Injection,
    and starts execution.  Never contains business logic.

    Wiring order (from diagram):
        1. load config.json
        2. instantiate Sink  (Output plugin)
        3. instantiate Engine, injecting Sink
        4. instantiate Reader, injecting Engine
        5. call reader.run()
    """

    def bootstrap(self) -> None:
        config     = self._load_config("config.json")
        sink       = self._create_sink(config["output_type"])
        engine     = TransformationEngine(sink, config["analysis"])
        reader     = self._create_reader(config["input_type"],
                                         engine,
                                         config["data_path"])
        reader.run()

    @staticmethod
    def _load_config(path: str) -> dict: ...

    @staticmethod
    def _create_sink(output_type: str) -> DataSink:
        return OUTPUT_DRIVERS[output_type]()

    @staticmethod
    def _create_reader(input_type: str,
                       service: PipelineService,
                       data_path: str):
        return INPUT_DRIVERS[input_type](service, data_path)
