import pandas as pd # Importing Panda Library

def load_data(file_path):
    df = pd.read_csv(file_path) # df = DataFrame (Like Excel sheet)
    return df