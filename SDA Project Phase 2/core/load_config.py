import json
import pandas as pd
import ast  # For safe parsing of stringified dicts
import requests

def load_config(file_path: str) -> dict:
    if file_path.startswith("http"):
        # Browser fetch for config
        response = requests.get(file_path)
        if file_path.endswith(".json"):
            return response.json()
        elif file_path.endswith(".csv"):
            df = pd.read_csv(io.StringIO(response.text))
            config = df.set_index('key')['value'].to_dict()
            # Parse stringified
            for k, v in config.items():
                if isinstance(v, str) and (v.startswith('{') or v.startswith('[')):
                    try:
                        config[k] = ast.literal_eval(v)
                    except (ValueError, SyntaxError):
                        pass
            return config
        else:
            raise ValueError(f"Unsupported browser config format: {file_path}")

    if file_path.endswith(".json"):
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
        # Assume columns 'key' and 'value'
        config = df.set_index('key')['value'].to_dict()
        # Parse stringified values (e.g., for nested dicts like 'analysis')
        for k, v in config.items():
            if isinstance(v, str) and (v.startswith('{') or v.startswith('[')):
                try:
                    config[k] = ast.literal_eval(v)
                except (ValueError, SyntaxError):
                    pass  # Leave as string if not parsable
        return config
    else:
        raise ValueError(f"Unsupported config format: {file_path}")