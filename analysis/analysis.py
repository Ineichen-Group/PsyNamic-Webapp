import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(".."))
from pandas.api.types import is_string_dtype


def get_df_from_dir(file_dir: str):
    files = [f for f in os.listdir(file_dir) if os.path.isfile(os.path.join(file_dir, f))]
    df_list = []
    for file in files:
        file_path = os.path.join(file_dir, file)
        df = pd.read_csv(file_path)
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)

import seaborn as sns
sns.set_style("whitegrid")

def compare_dfs(
    df_1: pd.DataFrame,
    df_2: pd.DataFrame,
    cols1: list[str],
    cols2: list[str],
) -> tuple[int, pd.DataFrame]:
    """
    Find matching rows between two DataFrames based on corresponding columns.
    String columns are compared case-insensitively.
    """

    if len(cols1) != len(cols2):
        raise ValueError("cols1 and cols2 must have the same length.")

    missing_1 = set(cols1) - set(df_1.columns)
    missing_2 = set(cols2) - set(df_2.columns)

    if missing_1:
        raise KeyError(f"Columns not found in df_1: {missing_1}")

    if missing_2:
        raise KeyError(f"Columns not found in df_2: {missing_2}")

    df1 = df_1.copy()
    df2 = df_2.copy()

    left_keys = []
    right_keys = []

    for i, (c1, c2) in enumerate(zip(cols1, cols2)):
        key1 = f"__key_{i}_df1"
        key2 = f"__key_{i}_df2"

        if is_string_dtype(df1[c1]) or is_string_dtype(df2[c2]):
            df1[key1] = df1[c1].astype("string").str.strip().str.lower()
            df2[key2] = df2[c2].astype("string").str.strip().str.lower()
        else:
            df1[key1] = df1[c1]
            df2[key2] = df2[c2]

        left_keys.append(key1)
        right_keys.append(key2)

    matches = df1.merge(
        df2,
        left_on=left_keys,
        right_on=right_keys,
        how="inner",
        suffixes=("_df1", "_df2"),
    )

    return len(matches), matches


 