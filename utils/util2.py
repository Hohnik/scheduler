import pandas as pd
from ortools.sat.python import cp_model

def data_to_dict_from(path) -> list[dict]:
    return pd.read_csv(path, dtype=str).to_dict(orient="records")
