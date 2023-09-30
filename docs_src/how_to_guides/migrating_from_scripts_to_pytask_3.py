# Content of task_data_management.py
import pandas as pd


def task_prepare_data() -> None:
    df = pd.read_csv("data.csv")

    # Many operations.

    df.to_pickle("data.pkl")
