import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(".."))

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
