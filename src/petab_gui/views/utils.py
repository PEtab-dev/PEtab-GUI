import pandas as pd
from petab.v1.C import (
    CONDITION_ID,
    MEASUREMENT,
    OBSERVABLE_ID,
    PARAMETER_ID,
    SIMULATION,
    TIME,
    X_OFFSET,
    Y_OFFSET,
)
from PySide6.QtCore import Qt


def proxy_to_dataframe(proxy_model):
    """Convert Proxy Model to pandas DataFrame."""
    rows = proxy_model.rowCount()
    cols = proxy_model.columnCount()

    if rows <= 1:  # <=1 due to "New row..." in every table
        return pd.DataFrame()

    headers = [proxy_model.headerData(c, Qt.Horizontal) for c in range(cols)]

    data = []
    for r in range(rows - 1):
        row = []
        for c in range(cols):
            value = proxy_model.index(r, c).data()
            # Convert empty strings to None
            row.append(
                None if (isinstance(value, str) and value == "") else value
            )
        data.append(row)

    if not data:
        return pd.DataFrame()

    # Create DataFrame in one shot
    df = pd.DataFrame(data, columns=headers)

    # Apply type-specific transformations
    table_type = proxy_model.source_model.table_type

    if table_type == "condition":
        df = df.set_index(CONDITION_ID)
    elif table_type == "observable":
        df = df.set_index(OBSERVABLE_ID)
    elif table_type == "parameter":
        df = df.set_index(PARAMETER_ID)
    elif table_type == "measurement":
        # Use pd.to_numeric with errors='coerce' for robust conversion
        df[MEASUREMENT] = pd.to_numeric(df[MEASUREMENT], errors="coerce")
        df[TIME] = pd.to_numeric(df[TIME], errors="coerce")
    elif table_type == "simulation":
        df[SIMULATION] = pd.to_numeric(df[SIMULATION], errors="coerce")
        df[TIME] = pd.to_numeric(df[TIME], errors="coerce")
    elif table_type == "visualization":
        if X_OFFSET in df.columns:
            df[X_OFFSET] = pd.to_numeric(df[X_OFFSET], errors="coerce")
        if Y_OFFSET in df.columns:
            df[Y_OFFSET] = pd.to_numeric(df[Y_OFFSET], errors="coerce")

    return df
