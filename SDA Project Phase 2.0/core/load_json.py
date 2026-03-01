import json
def load_json(file_path: str) -> dict:
    with open(file_path, "r") as file:
        data = json.load(file)
    return data