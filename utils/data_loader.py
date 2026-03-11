"""
data_loader.py
--------------
Responsible for loading and preprocessing the Global Superstore dataset.
All other analytics modules consume the DataFrame returned by load_data().
"""

import pandas as pd
import os


# Expected path to the dataset (relative to project root)
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "superstore.csv")


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    """
    Load the Global Superstore CSV dataset into a pandas DataFrame.

    Parameters
    ----------
    path : str
        Absolute or relative path to the CSV file.
        Defaults to data/superstore.csv relative to the project root.

    Returns
    -------
    pd.DataFrame
        Cleaned and type-cast DataFrame ready for analysis.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist at the given path.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at '{path}'. "
            "Please place superstore.csv inside the data/ directory."
        )

    # --- Load raw CSV -------------------------------------------------------
    df = pd.read_csv(path, encoding="latin-1")

    # --- Normalise column names (strip whitespace, title-case) --------------
    df.columns = df.columns.str.strip()

    # --- Parse date columns -------------------------------------------------
    date_columns = ["Order Date", "Ship Date"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # --- Compute derived columns -------------------------------------------
    if "Order Date" in df.columns and "Ship Date" in df.columns:
        # Shipping time in calendar days
        df["Shipping Days"] = (df["Ship Date"] - df["Order Date"]).dt.days

    # --- Ensure numeric types -----------------------------------------------
    numeric_cols = ["Sales", "Profit", "Quantity", "Discount"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Drop rows where Sales is entirely missing --------------------------
    df.dropna(subset=["Sales"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def get_date_range(df: pd.DataFrame):
    """Return (min_date, max_date) of Order Date as a convenience helper."""
    return df["Order Date"].min(), df["Order Date"].max()
