"""The Default Handlers for the GUI."""
import pandas as pd
import numpy as np
import copy

from collections import Counter
from ..C import (COPY_FROM, USE_DEFAULT, NO_DEFAULT, MIN_COLUMN, MAX_COLUMN,
                 MODE, DEFAULT_VALUE, SOURCE_COLUMN, SBML_LOOK)


class DefaultHandlerModel:
    def __init__(self, model, config, sbml_model = None):
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
        self._sbml_model = sbml_model

    def get_default(self, column_name, row_index=None, par_scale=None):
        """
        Get the default value for a column based on its strategy.
        :param column_name: The name of the column to compute the default for.
        :param row_index: Optional index of the row (needed for some strategies).
        :param par_scale: Optional parameter scale (needed for some strategies).
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
            return self._min_column(column_name, par_scale)
        elif strategy == MAX_COLUMN:
            return self._max_column(column_name, par_scale)
        elif strategy == COPY_FROM:
            return self._copy_column(column_name, column_config, row_index)
        elif strategy == MODE:
            column_config[SOURCE_COLUMN] = source_column
            return self._majority_vote(column_name, column_config)
        elif strategy == SBML_LOOK:
            return self._sbml_lookup(row_index)
        else:
            raise ValueError(f"Unknown strategy '{strategy}' for column '{column_name}'.")

    def _min_column(self, column_name, par_scale=None):
        if column_name not in self.model:
            return ""
        column_data = self.model[column_name].replace("", np.nan).dropna()
        if column_name in ["upperBound", "lowerBound"]:
            column_data = column_data.loc[
                self.model["parameterScale"] == par_scale
            ]
        if not column_data.empty:
            return column_data.min()

    def _max_column(self, column_name, par_scale=None):
        if column_name not in self.model:
            return ""
        column_data = self.model[column_name].replace("", np.nan).dropna()
        if column_name in ["upperBound", "lowerBound"]:
            column_data = column_data.loc[
                self.model["parameterScale"] == par_scale
            ]
        if not column_data.empty:
            return column_data.max()

    def _copy_column(self, column_name, config, row_index):
        source_column = config.get(SOURCE_COLUMN, column_name)
        source_column_valid = (
            source_column in self.model or source_column == self.model_index
        )
        if source_column and source_column_valid and row_index is not None:
            prefix = config.get("prefix", "")
            if row_index in self.model.index:
                if source_column == self.model_index:
                    return f"{prefix}{row_index}"
                value = f"{prefix}{self.model.at[row_index, source_column]}"
                return value if pd.notna(value) else ""
        return ""

    def _majority_vote(self, column_name, config):
        """Use the most frequent value in the column as the default.

        Defaults to last used value in case of a tie.
        """
        source_column = config.get(SOURCE_COLUMN, column_name)
        source_column_valid = (
            source_column in self.model or source_column == self.model_index
        )
        if source_column and source_column_valid:
            valid_values = copy.deepcopy(self.model[source_column][:-1])
            valid_values = valid_values.iloc[::-1]
            if valid_values.empty:
                return ""
            value_counts = Counter(valid_values)
            return value_counts.most_common(1)[0][0]
        return ""

    def _sbml_lookup(self, row_key):
        """Use the most frequent value in the column as the default.

        Defaults to last used value in case of a tie.
        """
        if self._sbml_model is None:
            return 1
        if row_key is None:
            return 1
        curr_model = self._sbml_model.get_current_sbml_model()
        if curr_model is None:
            return 1
        parameters = curr_model.get_valid_parameters_for_parameter_table()
        if row_key not in list(parameters):
            return 1
        return curr_model.get_parameter_value(row_key)
