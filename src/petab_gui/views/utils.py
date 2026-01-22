import pandas as pd
from PySide6.QtCore import Qt


def proxy_to_dataframe(proxy_model):
    """Convert Proxy Model to pandas DataFrame."""
    rows = proxy_model.rowCount()
    cols = proxy_model.columnCount()

    if rows <= 1:  # <=1 due to "New row..." in every table
        return pd.DataFrame()

    headers = [proxy_model.headerData(c, Qt.Horizontal) for c in range(cols)]

    # Pre-allocate list of lists (faster than dicts)
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
        df = df.set_index("conditionId")
    elif table_type == "observable":
        df = df.set_index("observableId")
    elif table_type == "parameter":
        df = df.set_index("parameterId")
    elif table_type == "measurement":
        # Use pd.to_numeric with errors='coerce' for robust conversion
        df["measurement"] = pd.to_numeric(df["measurement"], errors="coerce")
        df["time"] = pd.to_numeric(df["time"], errors="coerce")
    elif table_type == "simulation":
        df["simulation"] = pd.to_numeric(df["simulation"], errors="coerce")
        df["time"] = pd.to_numeric(df["time"], errors="coerce")
    elif table_type == "visualization":
        if "xOffset" in df.columns:
            df["xOffset"] = pd.to_numeric(df["xOffset"], errors="coerce")
        if "yOffset" in df.columns:
            df["yOffset"] = pd.to_numeric(df["yOffset"], errors="coerce")

    return df
