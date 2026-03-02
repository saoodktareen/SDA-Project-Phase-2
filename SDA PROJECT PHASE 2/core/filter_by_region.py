from .load_data import load_data
from .cleaner import clean_data
from .load_json import load_json

def filter_by_region(df, config:dict):
    if "region" in config: 
        if isinstance(config["region"], list): 
            df = df[df["Continent"].isin(config["region"])] 
        else: df = df[df["Continent"] == config["region"]] # Year filter 
    if "year" in config: 
        if isinstance(config["year"], list): 
            df = df[df["Year"].isin(config["year"])] 
        else: 
            df = df[df["Year"] == config["year"]] # Country filter 
    return df