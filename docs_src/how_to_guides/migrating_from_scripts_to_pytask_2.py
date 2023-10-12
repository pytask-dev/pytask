# Content of task_data_management.py
import pandas as pd


def main() -> None:
    df = pd.read_csv("data.csv")

    # Many operations.

    df.to_pickle("data.pkl")


if __name__ == "__main__":
    main()
