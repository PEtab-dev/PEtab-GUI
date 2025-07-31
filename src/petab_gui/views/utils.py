import pandas as pd
from PySide6.QtCore import Qt


def proxy_to_dataframe(proxy_model):
    rows = proxy_model.rowCount()
    cols = proxy_model.columnCount()

    headers = [proxy_model.headerData(c, Qt.Horizontal) for c in range(cols)]
    data = []

    for r in range(rows-1):
        row = {
            headers[c]: proxy_model.index(r, c).data()
            for c in range(cols)
        }
        for key, value in row.items():
            if isinstance(value, str) and value == "":
                row[key] = None
        data.append(row)
    if not data:
        return pd.DataFrame()
    if proxy_model.source_model.table_type == "condition":
        data = pd.DataFrame(data).set_index("conditionId")
    elif proxy_model.source_model.table_type == "observable":
        data = pd.DataFrame(data).set_index("observableId")
    elif proxy_model.source_model.table_type == "parameter":
        data = pd.DataFrame(data).set_index("parameterId")
    elif proxy_model.source_model.table_type == "measurement":
        # turn measurement and time to float
        data = pd.DataFrame(data)
        data["measurement"] = data["measurement"].astype(float)
        data["time"] = data["time"].astype(float)
    elif proxy_model.source_model.table_type == "simulation":
        # turn simulation and time to float
        data = pd.DataFrame(data)
        data["simulation"] = data["simulation"].astype(float)
        data["time"] = data["time"].astype(float)
    elif proxy_model.source_model.table_type == "visualization":
        data = pd.DataFrame(data)
        if "xOffset" in data.columns:
            data["xOffset"] = data["xOffset"].astype(float)
        if "yOffset" in data.columns:
            data["yOffset"] = data["yOffset"].astype(float)
    else:
        data = pd.DataFrame(data)

    return data
