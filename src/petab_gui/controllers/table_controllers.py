"""Classes for the controllers of the tables in the GUI."""
from PySide6.QtWidgets import QInputDialog, QMessageBox, QFileDialog, \
    QCompleter, QAbstractItemView
import numpy as np
import pandas as pd
import petab.v1 as petab
from PySide6.QtCore import Signal, QObject, QModelIndex, Qt, QTimer
from pathlib import Path
from ..models.pandas_table_model import PandasTableModel, \
    PandasTableFilterProxy
from ..views.table_view import TableViewer, SingleSuggestionDelegate, \
    ColumnSuggestionDelegate, ComboBoxDelegate, ParameterIdSuggestionDelegate
from ..utils import get_selected, process_file
from .utils import prompt_overwrite_or_append
from ..C import COLUMN
import re


class TableController(QObject):
    """Base class for table controllers."""
    overwritten_df = Signal()  # Signal to mother controller

    def __init__(
        self,
        view: TableViewer,
        model: PandasTableModel,
        logger,
        mother_controller
    ):
        """Initialize the table controller.

        Parameters
        ----------
        view: TableViewer
            The view of the table.
        model: PandasTableModel
            The model of the table.
        logger:
            Handles all logging tasks
        mother_controller: MainController
            The main controller of the application. Needed for signal
            forwarding.
        """
        super().__init__()
        self.view = view
        self.model = model
        self.model.view = self.view.table_view
        self.proxy_model = PandasTableFilterProxy(model)
        self.logger = logger
        self.check_petab_lint_mode = True
        self.mother_controller = mother_controller
        self.view.table_view.setModel(self.proxy_model)
        self.setup_connections()
        self.setup_connections_specific()

        self.completers = {}
        self.setup_completers()

    def setup_completers(self):
        pass

    def release_completers(self):
        """Sets the completers to None. Safety Measure."""
        if not self.completers:
            return
        for column_index in range(self.model.columnCount()):
            self.view.table_view.setItemDelegateForColumn(column_index, None)
        self.completers = {}

    def setup_connections_specific(self):
        """Will be implemented in child controllers."""
        pass

    def setup_connections(self):
        """Setup connections to the view.

        Only handles connections from within the table controllers.
        """
        self.model.new_log_message.connect(
            self.logger.log_message
        )
        self.model.cell_needs_validation.connect(
            self.validate_changed_cell
        )
        self.model.inserted_row.connect(
            self.set_index_on_new_row
        )

    def validate_changed_cell(self, row, column):
        """Validate the changed cell and whether its linting is correct."""
        if not self.check_petab_lint_mode:
            return
        row_data = self.model.get_df().iloc[row]
        index_name = self.model.get_df().index.name
        row_data = row_data.to_frame().T
        row_data.index.name = index_name
        try:
            self.check_petab_lint(row_data)
            for col in range(self.model.columnCount()):
                self.model.discard_invalid_cell(row, col)
            error_message = None
        except Exception as e:
            error_message = str(e)
            self.logger.log_message(
                f"PEtab linter failed at row {row}, column {column}: "
                f"{error_message}",
                color="red"
            )
        # Update invalid cells based on the error state
        if error_message:
            self.model.add_invalid_cell(row, column)
        else:
            self.model.discard_invalid_cell(row, column)
        self.model.notify_data_color_change(row, column)

    def open_table(self, file_path=None, separator=None, mode="overwrite"):
        if not file_path:
            # Open a file dialog to select the CSV or TSV file
            file_path, _ = QFileDialog.getOpenFileName(
                self.view, "Open CSV or TSV", "",
                "CSV/TSV/TXT Files (*.csv *.tsv *.txt)"
            )
        # just in case anything goes wrong here
        if not file_path:
            return
        # convert the file path to a Path object if it is a string
        if type(file_path) is str:
            file_path = Path(file_path)

        if separator is None:
            actionable, separator = process_file(file_path, self.logger)
            if actionable in ["yaml", "sbml", "data_matrix", None]:  # no table
                return
        try:
            if self.model.table_type == "measurement":
                new_df = pd.read_csv(file_path, sep=separator)
            else:
                new_df = pd.read_csv(file_path, sep=separator, index_col=0)
        except Exception as e:
            self.view.log_message(
                f"Failed to read file: {str(e)}",
                color="red"
            )
            return
        dtypes = {
            col: self.model._allowed_columns.get(
                col, {"type": np.object_}
            )["type"] for col in new_df.columns
        }
        new_df = new_df.astype(dtypes)
        if mode is None:
            mode = prompt_overwrite_or_append(self)
        # Overwrite or append the table with the new DataFrame
        if mode == "append":
            self.append_df(new_df)
        elif mode == "overwrite":
            self.overwrite_df(new_df)
            self.model.reset_invalid_cells()

    def overwrite_df(self, new_df: pd.DataFrame):
        # TODO: Mother controller connects to overwritten_df signal. Set df
        #  in petabProblem and unsaved changes to True
        """Overwrite the DataFrame of the model with the data from the view."""
        self.proxy_model.setSourceModel(None)
        self.model.beginResetModel()
        self.model._data_frame = new_df
        self.model.beginResetModel()
        self.logger.log_message(
            f"Overwrote the {self.model.table_type} table with new data.",
            color="green"
        )
        # test: overwrite the new model as source model
        self.proxy_model.setSourceModel(self.model)
        # change default sizing
        self.view.table_view.reset_column_sizes()
        self.overwritten_df.emit()

    def append_df(self, new_df: pd.DataFrame):
        """Append the DataFrame of the model with the data from the view.

        Merges two DataFrames:
            1. Columns are the union of both DataFrame columns.
            2. Rows are the union of both DataFrame rows (duplicates removed)
        """
        self.model.beginResetModel()
        combined_df = pd.concat(
            [self.model.get_df(), new_df], axis=0
        )
        combined_df = combined_df[~combined_df.index.duplicated(keep="first")]
        self.model._data_frame = combined_df
        self.proxy_model.setSourceModel(None)
        self.proxy_model.setSourceModel(self.model)
        self.model.endResetModel()
        self.logger.log_message(
            f"Appended the {self.model.table_type} table with new data.",
            color="green"
        )
        # test: overwrite the new model as source model
        self.overwritten_df.emit()

    def clear_table(self):
        """Clear the table."""
        self.model.clear_table()

    def delete_row(self):
        """Delete the selected row(s) from the table."""
        table_view = self.view.table_view

        selected_rows = get_selected(table_view)
        if not selected_rows:
            return
        self.model.update_invalid_cells(selected_rows, mode="rows")
        for row in sorted(selected_rows, reverse=True):
            if row >= self.model.rowCount() - 1:
                continue
            self.model.delete_row(row)
            self.logger.log_message(
                f"Deleted row {row} from {self.model.table_type} table."
                f" Data: {self.model.get_df().iloc[row].to_dict()}",
                color="orange"
            )
        self.model.something_changed.emit(True)

    def add_row(self):
        """Add a row to the datatable"""
        row_count = self.model.rowCount() - 1
        if self.model.insertRows(row_count, 1):
            new_row_index = self.model.index(row_count, 0)

            selection_model = self.view.table_view.selectionModel()
            if selection_model:
                selection_model.select(
                    new_row_index,
                    selection_model.SelectionFlag.ClearAndSelect
                )
            self.view.table_view.scrollTo(new_row_index)
            self.view.table_view.setCurrentIndex(new_row_index)

    def delete_column(self):
        """Delete the selected column(s) from the table."""
        table_view = self.view.table_view

        selected_columns = get_selected(table_view, mode=COLUMN)
        if not selected_columns:
            return
        deleted_columns = set()
        for column in sorted(selected_columns, reverse=True):
            # safely delete potential item delegates
            allow_del, column_name = self.model.allow_column_deletion(column)
            if not allow_del:
                self.logger.log_message(
                    f"Cannot delete column {column_name}, as it is a "
                    f"required column!",
                    color = "red"
                )
                continue
            if column_name in self.completers:
                self.view.table_view.setItemDelegateForColumn(column, None)
                del self.completers[column_name]
            self.model.delete_column(column)
            self.logger.log_message(
                f"Deleted column '{column_name}' from {self.model.table_type} table.",
                color="orange"
            )
            deleted_columns.add(column)
        self.model.update_invalid_cells(deleted_columns, mode="columns")
        self.model.something_changed.emit(True)

    def add_column(self, column_name: str = None):
        """Add a column to the datatable"""
        if not column_name:
            column_name, ok = QInputDialog.getText(
                self.view,
                "Add Column",
                "Enter the name of the new column:"
            )
            if not ok:
                return
        self.model.insertColumn(column_name)

    def set_index_on_new_row(self, index: QModelIndex):
        """Set the index of the model when a new row is added."""
        self.view.table_view.setCurrentIndex(index)

    def filter_table(self, text):
        """Filter the table."""
        self.proxy_model.setFilterRegularExpression(text)
        self.proxy_model.setFilterKeyColumn(-1)

    def remove_filter(self):
        """Remove the filter from the table."""
        self.proxy_model.setFilterRegularExpression("")
        self.proxy_model.setFilterKeyColumn(-1)

    def copy_to_clipboard(self):
        """Copy the currently selected cells to the clipboard."""
        self.view.copy_to_clipboard()

    def paste_from_clipboard(self):
        """Paste the clipboard content to the currently selected cells."""
        self.check_petab_lint_mode = False
        self.view.paste_from_clipboard()
        self.check_petab_lint_mode = True
        try:
            self.check_petab_lint()
        except Exception as e:
            self.logger.log_message(
                f"PEtab linter failed after copying: {str(e)}",
                color="red"
            )

    def check_petab_lint(self, row_data):
        """Check a single row of the model with petablint."""
        raise NotImplementedError(
            "This method must be implemented in child classes."
        )

    def find_text(
        self, text, case_sensitive=False, regex=False, whole_cell=False
    ):
        """Efficiently find all matching cells."""
        df = self.model.get_df()

        # Search in the main DataFrame
        if regex:
            pattern = re.compile(text, 0 if case_sensitive else re.IGNORECASE)
            mask = df.map(lambda cell: bool(pattern.fullmatch(str(cell))) if whole_cell else bool(pattern.search(str(cell))))
        else:
            text = text.lower() if not case_sensitive else text
            mask = df.map(lambda cell: text == str(cell).lower() if whole_cell else text in str(cell).lower()) if not case_sensitive else \
                   df.map(lambda cell: text == str(cell) if whole_cell else text in str(cell))

        # Find matches
        match_indices = list(zip(*mask.to_numpy().nonzero()))
        table_matches = [(row, col + self.model.column_offset) for row, col in match_indices]

        # Search in the index if it's named
        index_matches = []
        if isinstance(df.index, pd.Index) and df.index.name:
            if regex:
                index_mask = df.index.to_series().map(lambda idx: bool(pattern.fullmatch(str(idx))) if whole_cell else bool(pattern.search(str(idx))))
            else:
                index_mask = df.index.to_series().map(lambda idx: text == str(idx).lower() if whole_cell else text in str(idx).lower()) if not case_sensitive else \
                             df.index.to_series().map(lambda idx: text == str(idx) if whole_cell else text in str(idx))

            index_matches = [(df.index.get_loc(idx), 0) for idx in index_mask[index_mask].index]

        all_matches = index_matches + table_matches

        # 🔹 Highlight matched text
        self.highlight_text(all_matches)
        return all_matches

    def highlight_text(self, matches):
        """Color the text of all matched cells in yellow."""
        self.model.highlighted_cells = set(matches)
        top_left = self.model.index(0, 0)
        bottom_right = self.model.index(self.model.rowCount() - 1,
                                        self.model.columnCount() - 1)
        self.model.dataChanged.emit(top_left, bottom_right,
                                    [Qt.ForegroundRole])

    def cleanse_highlighted_cells(self):
        """Cleanses the highlighted cells."""
        self.model.highlighted_cells = set()
        top_left = self.model.index(0, 0)
        bottom_right = self.model.index(self.model.rowCount() - 1,
                                        self.model.columnCount() - 1)
        self.model.dataChanged.emit(top_left, bottom_right,
                                    [Qt.ForegroundRole])

    def focus_match(self, match):
        """Focus and select the given match in the table."""
        if match is None:
            self.view.table_view.clearSelection()
            return
        row, col = match
        index = self.model.index(row, col)
        if not index.isValid():
            return
        proxy_index = self.view.table_view.model().mapFromSource(index)
        if not proxy_index.isValid():
            return

        self.view.table_view.setCurrentIndex(proxy_index)
        self.view.table_view.setCurrentIndex(proxy_index)
        self.view.table_view.scrollTo(
                proxy_index, QAbstractItemView.EnsureVisible
        )

    def replace_text(self, row, col, replace_text, search_text, case_sensitive, regex):
        """Replace the text in the given cell and update highlights."""
        index = self.model.index(row, col)
        original_text = self.model.data(index, Qt.DisplayRole)

        if not original_text:
            return

        if regex:
            pattern = re.compile(search_text, 0 if case_sensitive else re.IGNORECASE)
            new_text = pattern.sub(replace_text, original_text)
        else:
            if not case_sensitive:
                search_text = re.escape(search_text.lower())
                new_text = re.sub(search_text, replace_text, original_text, flags=re.IGNORECASE)
            else:
                new_text = original_text.replace(search_text, replace_text)

        if new_text != original_text:
            self.model.setData(index, new_text, Qt.EditRole)
            self.model.highlighted_cells.discard((row, col))
            self.model.dataChanged.emit(index, index, [Qt.DisplayRole])

    def replace_all(
        self, search_text, replace_text, case_sensitive=False, regex=False
    ):
        """Replace all occurrences of the search term in the Model."""
        if not search_text or not replace_text:
            return

        df = self.model._data_frame
        if regex:
            pattern = re.compile(search_text,
                                 0 if case_sensitive else re.IGNORECASE)
            df.replace(to_replace=pattern, value=replace_text, regex=True,
                       inplace=True)
        else:
            if not case_sensitive:
                df.replace(
                    to_replace=re.escape(search_text),
                    value=replace_text,
                    regex=True,
                    inplace=True
                )
            else:
                df.replace(to_replace=search_text, value=replace_text,
                           inplace=True)

        # Replace in the index as well
        if isinstance(df.index, pd.Index) and df.index.name:
            index_map = {
                idx: pattern.sub(replace_text, str(idx)) if regex else str(
                    idx).replace(search_text, replace_text)
                for idx in df.index if search_text in str(idx)}
            if index_map:
                df.rename(index=index_map, inplace=True)


class MeasurementController(TableController):
    """Controller of the Measurement table."""

    def check_petab_lint(self, row_data: pd.DataFrame = None):
        """Check a number of rows of the model with petablint."""
        if row_data is None:
            row_data = self.model.get_df()
        # Can this be done more elegantly?
        observable_df = self.mother_controller.model.observable.get_df()
        return petab.check_measurement_df(
            row_data,
            observable_df=observable_df,
        )

    def rename_value(self, old_id: str, new_id: str, column_names: str | list[str]):
        """Rename the observables in the measurement_df.

        Triggered by changes in the original observable_df id.

        Parameters
        ----------
        old_id:
            The old observable_id, which was changed.
        new_id:
            The new observable_id.
        """
        if not isinstance(column_names, list):
            column_names = [column_names]

        # Find occurences
        mask = self.model._data_frame[column_names].eq(old_id)
        if mask.any().any():
            self.model._data_frame.loc[mask] = new_id
            changed_rows = mask.any(axis=1)
            first_row, last_row = (
                changed_rows.idxmax(), changed_rows[::-1].idxmax()
            )
            top_left = self.model.index(first_row, 1)
            bottom_right = self.model.index(
                last_row, self.model.columnCount() - 1
            )
            self.model.dataChanged.emit(
                top_left, bottom_right, [Qt.DisplayRole, Qt.EditRole]
            )

            # Emit change signal
            self.model.something_changed.emit(True)

    def copy_noise_parameters(
        self,
        observable_id: str,
        condition_id: str | None = None
    ) -> str:
        """Copies noise parameter from measurements already in the table.

        Measurements of similar observables are most likely assumed to
        share a noise model. Therefore, noise parameters are copied. Prefers
        matching condition_id to copy. If not Matching condition_id,
        will copy from any matching row.

        Parameters:
        ----------
        observable_id:
            The observable_id of the new measurement.
        condition_id:
            The condition_id of the new measurement.

        Returns:
            The noise parameter that has been copied, or "" if no noise
            parameter could be copied.
        """
        measurement_df = self.model.measurement._data_frame
        matching_rows = measurement_df[
            measurement_df["observableId"] == observable_id]
        if matching_rows.empty:
            return ""
        if not condition_id:
            return matching_rows["noiseParameters"].iloc[0]
        preferred_row = matching_rows[
            matching_rows["simulationConditionId"] == condition_id]
        if not preferred_row.empty:
            return preferred_row["noiseParameters"].iloc[0]
        else:
            return matching_rows["noiseParameters"].iloc[0]

    def upload_data_matrix(self):
        """Upload a data matrix to the measurement table.

        Opens a FileDialog to select a CSV file with the data matrix.
        The data matrix is a CSV file with the following columns:
        - time: Either "Time", "time" or "t". Time points of the measurements.
        - observable_ids: Observables measured at the given timepoints.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self.view,
            "Open Data Matrix",
            "",
            "CSV Files (*.csv);;TSV Files (*.tsv)"
        )
        if file_name:
            self.process_data_matrix_file(file_name)

    def process_data_matrix_file(self, file_name, mode, separator=None):
        """Process the data matrix file.

        Upload the data matrix. Then populate the measurement table with the
        new measurements. Additionally, triggers checks for observable_ids.
        """
        try:
            data_matrix = self.load_data_matrix(file_name, separator)
            if data_matrix is None or data_matrix.empty:
                return

            condition_id = "cond1"  # Does this need adjustment?
            if mode == "overwrite":
                self.model.clear_table()
            self.populate_tables_from_data_matrix(data_matrix, condition_id)
            self.model.something_changed.emit(True)

        except Exception as e:
            self.logger.log_message(
                f"An error occurred while uploading the data matrix: {str(e)}",
                color="red"
            )

    def load_data_matrix(self, file_name, separator=None):
        """Loads in the data matrix. Checks for the 'time' column."""
        data_matrix = pd.read_csv(
            file_name, delimiter=separator
        )
        if not any(
            col in data_matrix.columns for col in ["Time", "time", "t"]):
            self.logger.log_message(
                "Invalid File, the file must contain a 'Time' column. "
                "Please ensure that the file contains a 'Time'",
                color="red"
            )
            return None

        time_column = next(
            col for col in ["Time", "time", "t"] if col in data_matrix.columns
        )
        return data_matrix.rename(columns={time_column: "time"})

    def populate_tables_from_data_matrix(self, data_matrix, condition_id):
        """Populate the measurement table from the data matrix."""
        for col in data_matrix.columns:
            if col == "time":
                continue
            observable_id = col
            self.model.possibly_new_condition.emit(observable_id)
            self.model.possibly_new_observable.emit(condition_id)
            self.add_measurement_rows(
                data_matrix[["time", observable_id]],
                observable_id,
                condition_id
            )

    def add_measurement_rows(self, data_matrix, observable_id, condition_id):
        """Adds multiple rows to the measurement table."""
        # check number of rows and signal row insertion
        rows = data_matrix.shape[0]
        # get current number of rows
        current_rows = self.model.get_df().shape[0]
        self.model.insertRows(position=None,
                              rows=rows)  # Fills the table with empty rows
        top_left = self.model.createIndex(current_rows, 0)
        for i_row, (_, row) in enumerate(data_matrix.iterrows()):
            self.model.fill_row(
                i_row + current_rows,
                data={
                    "observableId": observable_id,
                    "time": row["time"],
                    "measurement": row[observable_id],
                    "simulationConditionId": condition_id,
                }
            )
        bottom, right = (x - 1 for x in self.model.get_df().shape)
        bottom_right = self.model.createIndex(bottom, right)
        self.model.dataChanged.emit(top_left, bottom_right)
        self.logger.log_message(
            f"Added {rows} measurements to the measurement table.",
            color="green"
        )

    def setup_completers(self):
        """Set completers for the measurement table."""
        table_view = self.view.table_view
        # observableId
        observableId_index = self.model.return_column_index("observableId")
        if observableId_index > -1:
            self.completers["observableId"] = ColumnSuggestionDelegate(
                self.mother_controller.model.observable, "observableId"
            )
            table_view.setItemDelegateForColumn(
                observableId_index,
                self.completers["observableId"]
            )
        # preequilibrationConditionId
        preequilibrationConditionId_index = self.model.return_column_index(
            "preequilibrationConditionId"
        )
        if preequilibrationConditionId_index > -1:
            self.completers[
                "preequilibrationConditionId"] = ColumnSuggestionDelegate(
                self.mother_controller.model.condition, "conditionId"
            )
            table_view.setItemDelegateForColumn(
                preequilibrationConditionId_index,
                self.completers["preequilibrationConditionId"]
            )
        # simulationConditionId
        simulationConditionId_index = self.model.return_column_index(
            "simulationConditionId"
        )
        if simulationConditionId_index > -1:
            self.completers[
                "simulationConditionId"] = ColumnSuggestionDelegate(
                self.mother_controller.model.condition, "conditionId"
            )
            table_view.setItemDelegateForColumn(
                simulationConditionId_index,
                self.completers["simulationConditionId"]
            )
        # noiseParameters
        noiseParameters_index = self.model.return_column_index(
            "noiseParameters")
        if noiseParameters_index > -1:
            self.completers["noiseParameters"] = SingleSuggestionDelegate(
                self.model, "observableId", afix="sd_"
            )
            table_view.setItemDelegateForColumn(
                noiseParameters_index,
                self.completers["noiseParameters"]
            )


class ConditionController(TableController):
    """Controller of the Condition table."""
    condition_2be_renamed = Signal(str, str)  # Signal to mother controller

    def setup_connections_specific(self):
        """Setup connections specific to the condition controller.

        Only handles connections from within the table controllers.
        """
        self.model.relevant_id_changed.connect(
            self.maybe_rename_condition
        )

    def check_petab_lint(self, row_data: pd.DataFrame = None):
        """Check a number of rows of the model with petablint."""
        if row_data is None:
            row_data = self.model.get_df()
        observable_df = self.mother_controller.model.observable.get_df()
        sbml_model = self.mother_controller.model.sbml.get_current_sbml_model()
        return petab.check_condition_df(
            row_data,
            observable_df=observable_df,
            model=sbml_model,
        )

    def maybe_rename_condition(self, new_id, old_id):
        """Potentially rename condition_ids in measurement_df.

        Opens a dialog to ask the user if they want to rename the conditions.
        If so, emits a signal to rename the conditions in the measurement_df.
        """
        if old_id not in self.mother_controller.measurement_controller.model.get_df()["simulationConditionId"].values:
            return
        reply = QMessageBox.question(
            self.view, 'Rename Condition',
            f'Do you want to rename condition "{old_id}" to "{new_id}" '
            f'in all measurements?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.logger.log_message(
                f"Renaming condition '{old_id}' to '{new_id}' in all "
                f"measurements",
                color="green"
            )
            self.condition_2be_renamed.emit(old_id, new_id)


    def maybe_add_condition(self, condition_id, old_id=None):
        """Add a condition to the condition table if it does not exist yet."""
        if condition_id in self.model.get_df().index or not condition_id:
            return
        # add a row
        self.model.insertRows(position=None, rows=1)
        self.model.fill_row(
            self.model.get_df().shape[0] - 1,
            data={"conditionId": condition_id}
        )
        self.model.cell_needs_validation.emit(
            self.model.get_df().shape[0] - 1, 0
        )
        self.logger.log_message(
            f"Automatically added condition '{condition_id}' to the condition "
            f"table.",
            color="green"
        )

    def setup_completers(self):
        """Set completers for the condition table."""
        table_view = self.view.table_view
        # conditionName
        conditionName_index = self.model.return_column_index("conditionName")
        if conditionName_index > -1:
            self.completers["conditionName"] = SingleSuggestionDelegate(
                self.model, "conditionId")
            table_view.setItemDelegateForColumn(
                conditionName_index,
                self.completers["conditionName"]
            )
        for column in self.model.get_df().columns:
            if column in ["conditionId", "conditionName"]:
                continue
            column_index = self.model.return_column_index(column)
            if column_index > -1:
                self.completers[column] = ColumnSuggestionDelegate(
                    self.model, column, QCompleter.PopupCompletion
                )
                table_view.setItemDelegateForColumn(
                    column_index,
                    self.completers[column]
                )


class ObservableController(TableController):
    """Controller of the Observable table."""
    observable_2be_renamed = Signal(str, str)  # Signal to mother controller

    def setup_completers(self):
        """Set completers for the observable table."""
        table_view = self.view.table_view
        # observableName
        observableName_index = self.model.return_column_index("observableName")
        if observableName_index > -1:
            self.completers["observableName"] = SingleSuggestionDelegate(
                self.model, "observableId")
            table_view.setItemDelegateForColumn(
                observableName_index,
                self.completers["observableName"]
            )
        # observableTransformation
        observableTransformation_index = self.model.return_column_index(
            "observableTransformation"
        )
        if observableTransformation_index > -1:
            self.completers["observableTransformation"] = ComboBoxDelegate(
                ["lin", "log", "log10"]
            )
            table_view.setItemDelegateForColumn(
                observableTransformation_index,
                self.completers["observableTransformation"]
            )
        # noiseFormula
        noiseFormula_index = self.model.return_column_index("noiseFormula")
        if noiseFormula_index > -1:
            self.completers["noiseFormula"] = SingleSuggestionDelegate(
                self.model, "observableId", afix="noiseParameter1_"
            )
            table_view.setItemDelegateForColumn(
                noiseFormula_index,
                self.completers["noiseFormula"]
            )
        # noiseDistribution
        noiseDistribution_index = self.model.return_column_index(
            "noiseDistribution"
        )
        if noiseDistribution_index > -1:
            self.completers["noiseDistribution"] = ComboBoxDelegate(
                ["normal", "laplace"]
            )
            table_view.setItemDelegateForColumn(
                noiseDistribution_index,
                self.completers["noiseDistribution"]
            )

    def setup_connections_specific(self):
        """Setup connections specific to the observable controller.

        Only handles connections from within the table controllers.
        """
        self.model.relevant_id_changed.connect(
            self.maybe_rename_observable
        )

    def check_petab_lint(self, row_data: pd.DataFrame = None):
        """Check a number of rows of the model with petablint."""
        if row_data is None:
            row_data = self.model.get_df()
        return petab.check_observable_df(row_data)

    def maybe_rename_observable(self, new_id, old_id):
        """Potentially rename observable_ids in measurement_df.

        Opens a dialog to ask the user if they want to rename the observables.
        If so, emits a signal to rename the observables in the measurement_df.
        """
        if old_id not in self.mother_controller.measurement_controller.model.get_df()["observableId"].values:
            return
        reply = QMessageBox.question(
            self.view, 'Rename Observable',
            f'Do you want to rename observable "{old_id}" to "{new_id}" '
            f'in all measurements?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.logger.log_message(
                f"Renaming observable '{old_id}' to '{new_id}' in all "
                f"measurements",
                color="green"
            )
            # TODO: connect this signal with the measurement function
            self.observable_2be_renamed.emit(old_id, new_id)

    def maybe_add_observable(self, observable_id, old_id=None):
        """Add an observable to the observable table if it does not exist yet.

        Currently, `old_id` is not used.
        """
        if observable_id in self.model.get_df().index or not observable_id:
            return
        # add a row
        self.model.insertRows(position=None, rows=1)
        self.model.fill_row(
            self.model.get_df().shape[0] - 1,
            data={"observableId": observable_id}
        )
        self.model.cell_needs_validation.emit(
            self.model.get_df().shape[0] - 1, 0
        )
        self.logger.log_message(
            f"Automatically added observable '{observable_id}' to the "
            f"observable table.",
            color="green"
        )


class ParameterController(TableController):
    """Controller of the Parameter table."""

    def setup_completers(self):
        """Set completers for the parameter table."""
        table_view = self.view.table_view
        # parameterName
        parameterName_index = self.model.return_column_index("parameterName")
        if parameterName_index > -1:
            self.completers["parameterName"] = SingleSuggestionDelegate(
                self.model, "parameterId")
            table_view.setItemDelegateForColumn(
                parameterName_index,
                self.completers["parameterName"]
            )
        # parameterScale
        parameterScale_index = self.model.return_column_index("parameterScale")
        if parameterScale_index > -1:
            self.completers["parameterScale"] = ComboBoxDelegate(
                ["lin", "log", "log10"]
            )
            table_view.setItemDelegateForColumn(
                parameterScale_index,
                self.completers["parameterScale"]
            )
        # lowerBound
        lowerBound_index = self.model.return_column_index("lowerBound")
        if lowerBound_index > -1:
            self.completers["lowerBound"] = ColumnSuggestionDelegate(
                self.model, "lowerBound", QCompleter.PopupCompletion
            )
            table_view.setItemDelegateForColumn(
                lowerBound_index,
                self.completers["lowerBound"]
            )
        # upperBound
        upperBound_index = self.model.return_column_index("upperBound")
        if upperBound_index > -1:
            self.completers["upperBound"] = ColumnSuggestionDelegate(
                self.model, "upperBound", QCompleter.PopupCompletion
            )
            table_view.setItemDelegateForColumn(
                upperBound_index,
                self.completers["upperBound"]
            )
        # estimate
        estimate_index = self.model.return_column_index("estimate")
        if estimate_index > -1:
            self.completers["estimate"] = ComboBoxDelegate(
                ["1", "0"]
            )
            table_view.setItemDelegateForColumn(
                estimate_index,
                self.completers["estimate"]
            )
        # parameterId: retrieved from the sbml model
        parameterId_index = self.model.return_column_index("parameterId")
        sbml_model = self.mother_controller.model.sbml
        if parameterId_index > -1:
            self.completers["parameterId"] = ParameterIdSuggestionDelegate(
                par_model=self.model,
                sbml_model=sbml_model
            )
            table_view.setItemDelegateForColumn(
                parameterId_index,
                self.completers["parameterId"]
            )

    def check_petab_lint(self, row_data: pd.DataFrame = None):
        """Check a number of rows of the model with petablint."""
        if row_data is None:
            row_data = self.model.get_df()
        observable_df = self.mother_controller.model.observable.get_df()
        measurement_df = self.mother_controller.model.measurement.get_df()
        condition_df = self.mother_controller.model.condition.get_df()
        sbml_model = self.mother_controller.model.sbml.get_current_sbml_model()
        return petab.check_parameter_df(
            row_data,
            observable_df=observable_df,
            measurement_df=measurement_df,
            condition_df=condition_df,
            model=sbml_model,
        )
