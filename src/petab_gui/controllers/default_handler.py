"""The Default Handlers for the GUI."""
import pandas as pd
import numpy as np
import copy

from collections import Counter
from ..C import (COPY_FROM, USE_DEFAULT, NO_DEFAULT, MIN_COLUMN, MAX_COLUMN,
                 MODE, DEFAULT_VALUE, SOURCE_COLUMN, STRATEGIES_DEFAULT)


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
        source_column = column_name
        if column_name not in self.config:
            if "default_config" in self.config:
                column_name = "default_config"
            else:
                return ""

        column_config = self.config[column_name]
        strategy = column_config.get("strategy", NO_DEFAULT)
        default_value = column_config.get(DEFAULT_VALUE, "")

        if strategy == USE_DEFAULT:
            return default_value
        elif strategy == NO_DEFAULT:
            return ""
        elif strategy == MIN_COLUMN:
            return self._min_column(column_name, column_config)
        elif strategy == MAX_COLUMN:
            return self._max_column(column_name, column_config)
        elif strategy == COPY_FROM:
            return self._copy_column(column_name, column_config, row_index)
        elif strategy == MODE:
            column_config[SOURCE_COLUMN] = source_column
            return self._majority_vote(column_name, column_config)
        else:
            raise ValueError(f"Unknown strategy '{strategy}' for column '{column_name}'.")

    def _min_column(self, column_name):
        if column_name in self.model:
            column_data = self.model[column_name].replace("", np.nan).dropna()
            if not column_data.empty:
                return column_data.min()
        return ""

    def _max_column(self, column_name):
        if column_name in self.model:
            column_data = self.model[column_name].replace("", np.nan).dropna()
            if not column_data.empty:
                return column_data.max()
        return ""

    def _copy_column(self, column_name, config, row_index):
        source_column = config.get("source_column", None)
        source_column_valid = (
            source_column in self.model or source_column == self.model_index
        )
        if source_column and source_column_valid and row_index is not None:
            prefix = config.get("prefix", "")
            if row_index in self.model.index:
                if source_column == self.model_index:
                    return f"{prefix}{row_index}"
                value = f"{prefix}{self.model.at[row_index, source_column]}"
                return value if pd.notna(value) else config.get("default_value", "")
        return config.get("default_value", "")

    def _majority_vote(self, column_name, config):
        """Use the most frequent value in the column as the default.

        Defaults to last used value in case of a tie.
        """
        source_column = config.get("source_column", None)
        source_column_valid = (
            source_column in self.model or source_column == self.model_index
        )
        if source_column and source_column_valid:
            valid_values = copy.deepcopy(self.model[source_column][:-1])
            valid_values = valid_values.iloc[::-1]
            if valid_values.empty:
                return config.get("default_value", "")
            value_counts = Counter(valid_values)
            return value_counts.most_common(1)[0][0]
        return config.get("default_value", "")