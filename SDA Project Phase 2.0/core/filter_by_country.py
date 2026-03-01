from .load_data import load_data
from .cleaner import clean_data
from .load_json import load_json

def filter_by_country(df, config:dict):
    if "country" in config: 
        if isinstance(config["country"], list): 
            df = df[df["Country Name"].isin(config["country"])] 
        else: df = df[df["Country Name"] == config["country"]]
    df = df.dropna(subset=["GDP"]) 
    return df