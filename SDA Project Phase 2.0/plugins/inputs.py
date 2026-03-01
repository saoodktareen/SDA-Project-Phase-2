from typing import List
from core.contracts import PipelineService
from core.load_data import load_data
from core.cleaner import clean_data
from core.transform import transform_to_long
import json
import pandas as pd

class CSVReader:
    def __init__(self, service: PipelineService, data_path: str):
        self.service = service
        self.data_path = data_path

    def run(self):
        df_wide = load_data(self.data_path)
        cleaned_wide, _ = clean_data(df_wide)
        df_long = transform_to_long(cleaned_wide)
        self.service.execute(df_long.to_dict("records"))

class JSONReader:
    def __init__(self, service: PipelineService, data_path: str):
        self.service = service
        self.data_path = data_path

    def run(self):
        with open(self.data_path) as f:
            data = json.load(f)  # List of dicts with text cols + year: GDP
        df_wide = pd.DataFrame(data)
        cleaned_wide, _ = clean_data(df_wide)
        df_long = transform_to_long(cleaned_wide)
        self.service.execute(df_long.to_dict("records"))