# Force UTF-8 encoding for stdout/stderr (Windows fix)
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

from typing import List
from core.contracts import PipelineService
import pandas as pd
import json
import requests
from bs4 import BeautifulSoup

class CSVReader:
    def __init__(self, service: PipelineService, data_path: str):
        self.service = service
        self.data_path = data_path

    def run(self):
        print("[DEBUG INPUT] Starting CSVReader...")
        df_wide = pd.read_csv(self.data_path)
        print(f"[DEBUG INPUT] Loaded CSV with shape: {df_wide.shape}")
        records = df_wide.to_dict("records")
        print(f"[DEBUG INPUT] Sending {len(records)} raw records to core engine")
        self.service.execute(records)

class JSONReader:
    def __init__(self, service: PipelineService, data_path: str):
        self.service = service
        self.data_path = data_path

    def run(self):
        print("[DEBUG INPUT] Starting JSONReader...")
        with open(self.data_path, "r") as f:
            raw = json.load(f)
        df_wide = pd.DataFrame(raw)
        print(f"[DEBUG INPUT] Loaded JSON with shape: {df_wide.shape}")
        records = df_wide.to_dict("records")
        print(f"[DEBUG INPUT] Sending {len(records)} raw records to core engine")
        self.service.execute(records)

class ExcelReader:
    def __init__(self, service: PipelineService, data_path: str):
        self.service = service
        self.data_path = data_path

    def run(self):
        print("[DEBUG INPUT] Starting ExcelReader...")
        df_wide = pd.read_excel(self.data_path, sheet_name="GDP", engine="openpyxl")
        print(f"[DEBUG INPUT] Loaded Excel with shape: {df_wide.shape}")
        records = df_wide.to_dict("records")
        print(f"[DEBUG INPUT] Sending {len(records)} raw records to core engine")
        self.service.execute(records)

class BrowserReader:
    def __init__(self, service: PipelineService, data_path: str):  # data_path = URL
        self.service = service
        self.data_path = data_path

    def run(self):
        print("[DEBUG INPUT] Starting BrowserReader...")
        try:
            response = requests.get(self.data_path)
            response.raise_for_status()  # Raise error for bad status
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Example: Try to find a table (adapt this parsing logic to your actual source)
            table = soup.find('table')
            if table:
                df_wide = pd.read_html(str(table))[0]
                # Add Continent placeholder if not present
                if 'Continent' not in df_wide.columns:
                    df_wide['Continent'] = 'Unknown'
                print(f"[DEBUG INPUT] Parsed HTML table with shape: {df_wide.shape}")
                records = df_wide.to_dict("records")
            else:
                print("[DEBUG INPUT] No table found in HTML - sending empty records")
                records = []
                
            print(f"[DEBUG INPUT] Sending {len(records)} raw records to core engine")
            self.service.execute(records)
            
        except Exception as e:
            print(f"[ERROR BrowserReader] Failed to fetch/parse: {str(e)}")
            self.service.execute([])  # Send empty to avoid crash