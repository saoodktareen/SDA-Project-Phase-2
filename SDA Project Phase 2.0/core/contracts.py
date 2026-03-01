from typing import Protocol, List, Any, runtime_checkable

@runtime_checkable
class DataSink(Protocol):
    def write(self, records: List[dict]) -> None:
        ...

class PipelineService(Protocol):
    def execute(self, raw_data: List[Any]) -> None:
        ...