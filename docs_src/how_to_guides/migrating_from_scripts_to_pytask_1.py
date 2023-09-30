# Content of task_data_management.py
import pandas as pd


df = pd.read_csv("data.csv")

# Many operations.

df.to_pickle("data.pkl")
