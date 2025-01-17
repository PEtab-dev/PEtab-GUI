"""The Default Handlers for the GUI."""
import pandas as pd
import numpy as np

class DefaultHandlerModel:
    def __init__(self, model, config):
        """
        Initialize the handler for the model.
        :param model: The PandasTable Model containing the Data.
        :param config: Dictionary containing strategies and settings for each column.
        """
        self._model = model
        # TODO: Check what happens with non inplace operations
        self.model = model._data_frame
        self.config = config
        self.model_index = self.model.index.name

    def get_default(self, column_name, row_index=None):
        """
        Get the default value for a column based on its strategy.
        :param column_name: The name of the column to compute the default for.
        :param row_index: Optional index of the row (needed for some strategies).
        :return: The computed default value.
        """
        if column_name not in self.config:
            print(f"No configuration found for column '{column_name}'.")
            return ""

        column_config = self.config[column_name]
        strategy = column_config.get("strategy", "default_value")
        default_value = column_config.get("default_value", "")

        if strategy == "default_value":
            return default_value
        elif strategy == "min_column":
            return self._min_column(column_name, column_config)
        elif strategy == "max_column":
            return self._max_column(column_name, column_config)
        elif strategy == "copy_column":
            return self._copy_column(column_name, column_config, row_index)
        else:
            raise ValueError(f"Unknown strategy '{strategy}' for column '{column_name}'.")

    def _min_column(self, column_name, config):
        min_cap = config.get("min_cap", None)
        if column_name in self.model:
            # we have to drop "" values, as they are not considered as NaN
            column_data = self.model[column_name].replace("", np.nan).dropna()
            if not column_data.empty:
                min_value = column_data.min()
                return max(min_value, min_cap) if min_cap is not None else min_value
        return config.get("default_value", "")

    def _max_column(self, column_name, config):
        max_cap = config.get("max_cap", None)
        if column_name in self.model:
            column_data = self.model[column_name].replace("", np.nan).dropna()
            if not column_data.empty:
                max_value = column_data.max()
                return min(max_value, max_cap) if max_cap is not None else max_value
        return config.get("default_value", "")

    def _copy_column(self, column_name, config, row_index):
        source_column = config.get("source_column", None)
        source_column_valid = (
            source_column in self.model or source_column == self.model_index
        )
        if source_column and source_column_valid and row_index is not None:
            if row_index in self.model.index:
                if source_column == self.model_index:
                    return row_index
                value = self.model.at[row_index, source_column]
                return value if pd.notna(value) else config.get("default_value", "")
        return config.get("default_value", "")
