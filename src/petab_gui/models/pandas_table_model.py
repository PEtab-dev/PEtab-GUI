import pandas as pd
from PySide6.QtCore import (Qt, QAbstractTableModel, QModelIndex, Signal,
                            QSortFilterProxyModel, QMimeData)
from PySide6.QtGui import QColor, QBrush, QPalette
from PySide6.QtWidgets import QApplication
from ..C import COLUMNS
from ..utils import validate_value, create_empty_dataframe, is_invalid, \
    get_selected
from ..controllers.default_handler import DefaultHandlerModel
from ..settings_manager import settings_manager
from ..commands import (ModifyColumnCommand, ModifyRowCommand,
                        ModifyDataFrameCommand, RenameIndexCommand)


class PandasTableModel(QAbstractTableModel):
    """Basic table model for a pandas DataFrame."""
    # Signals
    relevant_id_changed = Signal(str, str, str)  # new_id, old_id, type
    new_log_message = Signal(str, str)  # message, color
    cell_needs_validation = Signal(int, int)  # row, column
    something_changed = Signal(bool)
    inserted_row = Signal(QModelIndex)
    fill_defaults = Signal(QModelIndex)

    def __init__(self, data_frame, allowed_columns, table_type,
                 undo_stack = None, parent=None):
        super().__init__(parent)
        self._allowed_columns = allowed_columns
        self.table_type = table_type
        self._invalid_cells = set()
        self.highlighted_cells = set()
        self._has_named_index = False
        if data_frame is None:
            data_frame = create_empty_dataframe(allowed_columns, table_type)
        self._data_frame = data_frame
        # add a view here, access is needed for selectionModels
        self.view = None
        # offset for row and column to get from the data_frame to the view
        self.row_index_offset = 0
        self.column_offset = 0
        # default values setup
        self.config = settings_manager.get_table_defaults(table_type)
        self.default_handler = DefaultHandlerModel(self, self.config)
        self.undo_stack = undo_stack

    def rowCount(self, parent=QModelIndex()):
        return self._data_frame.shape[0] + 1  # empty row at the end

    def columnCount(self, parent=QModelIndex()):
        return self._data_frame.shape[1] + self.column_offset

    def data(self, index, role=Qt.DisplayRole):
        """Return the data at the given index and role for the View."""
        if not index.isValid():
            return None
        row, column = index.row(), index.column()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if row == self._data_frame.shape[0]:
                if column == 0:
                    return f"New {self.table_type}"
                return ""
            if column == 0:
                value = self._data_frame.index[row]
                return str(value)
            value = self._data_frame.iloc[row, column - 1]
            if is_invalid(value):
                return ""
            return str(value)
        elif role == Qt.BackgroundRole:
            return self.determine_background_color(row, column)
        elif role == Qt.ForegroundRole:
            # Return yellow text if this cell is a match
            if (row, column) in self.highlighted_cells:
                return QApplication.palette().color(QPalette.HighlightedText)
            return QBrush(QColor(0, 0, 0))  # Default black text
        return None

    def flags(self, index):
        """Return whether cells are editable and selectable"""
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return the header data for the given section, orientation"""
        if role != Qt.DisplayRole:
            return None
        # role == Qt.DisplayRole
        if orientation == Qt.Horizontal:
            if section == 0:
                return self._data_frame.index.name
            else:
                return self._data_frame.columns[section - 1]
        if orientation == Qt.Vertical:
            return str(section)
        return None

    def insertRows(self, position, rows, parent=QModelIndex()) -> bool:
        """
        Insert new rows at the end of the DataFrame in-place.
        This function always adds rows at the end.

        Parameters:
        -----------
        position: Ignored, as rows are always inserted at the end.
        rows: The number of rows to add.
        parent: Unused in this implementation.

        Returns:
        --------
        bool: True if rows were added successfully.
        """
        if self.undo_stack:
            self.undo_stack.push(ModifyRowCommand(self, rows))
        else:
            # Fallback if undo stack isn't used
            command = ModifyRowCommand(self, rows)
            command.redo()
        return True

    def insertColumn(self, column_name: str):
        """
        Override insertColumn to always add the column at the right (end) of the table,
        and do so in-place on the DataFrame.
        """
        if column_name in self._data_frame.columns:
            self.new_log_message.emit(
                f"Column '{column_name}' already exists",
                "red"
            )
            return False
        if not (
            column_name in self._allowed_columns or
            self.table_type == "condition"
        ):  # empty dict means all columns allowed
            self.new_log_message.emit(
                f"Column '{column_name}' will be ignored for the petab "
                f"problem but may still be used to store relevant information",
                "orange"
            )

        if self.undo_stack:
            self.undo_stack.push(ModifyColumnCommand(self, column_name))
        else:
            # Fallback if undo stack isn't used
            command = ModifyColumnCommand(self, column_name)
            command.redo()

        return True

    def setData(self, index, value, role=Qt.EditRole):
        if not (index.isValid() and role == Qt.EditRole):
            return False

        if role != Qt.EditRole:
            return False

        if is_invalid(value) or value == "":
            value = None
        # check whether multiple rows but only one column is selected
        multi_row_change, selected = self.check_selection()
        if not multi_row_change:
            self.undo_stack.beginMacro("Set data")
            success = self._set_data_single(index, value)
            self.undo_stack.endMacro()
            return success
        # multiple rows but only one column is selected
        all_set = list()
        self.undo_stack.beginMacro("Set data")
        for index in selected:
            all_set.append(self._set_data_single(index, value))
        self.undo_stack.endMacro()
        return all(all_set)

    def _set_data_single(self, index, value):
        """Set the data of a single cell."""
        col_setoff = 0
        if self._has_named_index:
            col_setoff = 1
        if index.row() == self._data_frame.shape[0]:
            # empty row at the end
            self.insertRows(index.row(), 1)
            self.fill_defaults.emit(index)
            next_index = self.index(index.row(), 0)
            self.inserted_row.emit(next_index)
        if index.column() == 0 and self._has_named_index:
            return self.handle_named_index(index, value)
        row, column = index.row(), index.column()
        # Handling non-index (regular data) columns
        column_name = self._data_frame.columns[column - col_setoff]
        old_value = self._data_frame.iloc[row, column - col_setoff]
        # cast to numeric if necessary
        expected_type = self._allowed_columns.get(column_name, None)
        if is_invalid(value):
            change = {
                (self._data_frame.index[row], column_name): (old_value, None)}
            self.undo_stack.push(ModifyDataFrameCommand(self, change))
            self.cell_needs_validation.emit(row, column)
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        if expected_type:
            expected_type = expected_type["type"]
            value, error_message = validate_value(value, expected_type)
            if error_message:
                self.new_log_message.emit(
                    f"Column '{column_name}' expects a numeric value",
                    "red"
                )
                return False
        if value == old_value:
            return False

        if column_name == "observableId":
            change = {
                (self._data_frame.index[row], column_name): (old_value, value)}
            self.undo_stack.push(ModifyDataFrameCommand(self, change))
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            self.relevant_id_changed.emit(value, old_value, "observable")
            self.cell_needs_validation.emit(row, column)
            self.something_changed.emit(True)
            return True
        if column_name in ["conditionId", "simulationConditionId",
                           "preequilibrationConditionId"]:
            change = {
                (self._data_frame.index[row], column_name): (old_value, value)}
            self.undo_stack.push(ModifyDataFrameCommand(self, change))
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            self.relevant_id_changed.emit(value, old_value, "condition")
            self.cell_needs_validation.emit(row, column)
            self.something_changed.emit(True)
            return True

        # Validate data based on expected type
        expected_type = self._allowed_columns.get(column_name, None)
        if expected_type:
            expected_type = expected_type["type"]
            tried_value = value
            value, error_message = validate_value(
                value, expected_type
            )
            if error_message:
                self.new_log_message.emit(
                    f"Column '{column_name}' expects a value of "
                    f"type {expected_type}, but got '{tried_value}'",
                    "red"
                )
                return False
        # Set the new value
        change = {
            (self._data_frame.index[row], column_name): (old_value, value)}
        self.undo_stack.push(ModifyDataFrameCommand(self, change))
        # Validate the row after setting data
        self.cell_needs_validation.emit(row, column)
        self.something_changed.emit(True)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])

        return True

    def handle_named_index(self, index, value):
        """Handle the named index column."""
        pass

    def get_default_values(self, index):
        """Return the default values for a the row in a new index."""
        pass

    def replace_text(self, old_text: str, new_text: str):
        """Replace text in the table."""
        # find all occurences of old_text and sae indices
        mask = self._data_frame.eq(old_text)
        if mask.any().any():
            self._data_frame.replace(old_text, new_text, inplace=True)
            # Get first and last modified cell for efficient `dataChanged` emit
            changed_cells = mask.stack()[
                mask.stack()].index.tolist()  # Extract (row, col) pairs
            if changed_cells:
                first_row, first_col = changed_cells[0]
                last_row, last_col = changed_cells[-1]
                if self._has_named_index:
                    first_col += 1
                    last_col += 1
                top_left = self.index(first_row, first_col)
                bottom_right = self.index(last_row, last_col)
                self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])
        # also replace in the index
        if self._has_named_index and old_text in self._data_frame.index:
            self._data_frame.rename(index={old_text: new_text}, inplace=True)
            index_row = self._data_frame.index.get_loc(new_text)
            index_top_left = self.index(index_row, 0)
            index_bottom_right = self.index(index_row, 0)
            self.dataChanged.emit(
                index_top_left, index_bottom_right, [Qt.DisplayRole]
            )

    def get_df(self):
        """Return the DataFrame."""
        return self._data_frame

    def add_invalid_cell(self, row, column):
        """Add an invalid cell to the set."""
        # check that the index is valid
        if not self.index(row, column).isValid():
            return
        # return if it is the last row
        if row == self._data_frame.shape[0]:
            return
        # return if it is already invalid
        if (row, column) in self._invalid_cells:
            return
        self._invalid_cells.add((row, column))
        self.dataChanged.emit(
            self.index(row, column),
            self.index(row, column),
            [Qt.BackgroundRole]
        )

    def discard_invalid_cell(self, row, column):
        """Discard an invalid cell from the set."""
        self._invalid_cells.discard((row, column))
        self.dataChanged.emit(
            self.index(row, column),
            self.index(row, column),
            [Qt.BackgroundRole]
        )

    def update_invalid_cells(self, selected, mode: str = "rows"):
        """Edits the invalid cells when values are deleted."""
        if not selected:
            return
        old_invalid_cells = self._invalid_cells.copy()
        new_invalid_cells = set()
        sorted_to_del = sorted(selected)
        for a, b in old_invalid_cells:
            if mode == "rows":
                to_be_change = a
                not_changed = b
            elif mode == "columns":
                to_be_change = b
                not_changed = a
            if to_be_change in selected:
                continue
            smaller_count = sum(1 for x in sorted_to_del if x < to_be_change)
            new_val = to_be_change - smaller_count
            if mode == "rows":
                new_invalid_cells.add((new_val, not_changed))
            if mode == "columns":
                new_invalid_cells.add((not_changed, new_val))
        self._invalid_cells = new_invalid_cells

    def notify_data_color_change(self, row, column):
        """Notify the view to change the color of some cells"""
        self.dataChanged.emit(
            self.index(row, column),
            self.index(row, column),
            [Qt.BackgroundRole]
        )

    def get_value_from_column(self, column_name, row):
        """Retrieve the value from a specific column and row."""
        # if row is a new row return ""
        if row == self._data_frame.shape[0]:
            return ""
        if column_name in self._data_frame.columns:
            return self._data_frame.loc[row, column_name]
        if column_name == self._data_frame.index.name:
            return self._data_frame.index[row]
        return ""

    def return_column_index(self, column_name):
        """Return the index of a column. Defined in Subclasses"""
        pass

    def unique_values(self, column_name):
        """Return the unique values in a column."""
        if column_name in self._data_frame.columns:
            return list(self._data_frame[column_name].dropna().unique())
        if column_name == self._data_frame.index.name:
            return list(self._data_frame.index.dropna().unique())
        return []

    def delete_row(self, row):
        """Delete a row from the table."""
        if self.undo_stack:
            self.undo_stack.push(ModifyRowCommand(self, row, False))
        else:
            # Fallback if undo stack isn't used
            command = ModifyRowCommand(self, row, False)
            command.redo()

    def delete_column(self, column_index):
        """Delete a column from the DataFrame."""
        column_name = self._data_frame.columns[column_index - self.column_offset]
        if self.undo_stack:
            self.undo_stack.push(ModifyColumnCommand(self, column_name, False))
        else:
            # Fallback if undo stack isn't used
            command = ModifyColumnCommand(self, column_name, False)
            command.redo()

    def clear_table(self):
        """Clear the table."""
        self.beginResetModel()
        self._data_frame.drop(self._data_frame.index, inplace=True)
        self.endResetModel()

    def check_selection(self):
        """Check if multiple rows but only one column is selected."""
        if self.view is None:
            return False
        selected = get_selected(self.view, mode="index")
        cols = set([index.column() for index in selected])
        rows = set([index.row() for index in selected])
        return len(rows) > 1 and len(cols) == 1, selected

    def reset_invalid_cells(self):
        """Reset the invalid cells and update their background color."""
        if not self._invalid_cells:
            return

        invalid_cells = list(self._invalid_cells)
        self._invalid_cells.clear()  # Clear invalid cells set

        for row, col in invalid_cells:
            index = self.index(row, col)
            self.dataChanged.emit(index, index, [Qt.BackgroundRole])

    def mimeData(self, rectangle, start_index):
        """Return the data to be copied to the clipboard.

        Parameters
        ----------
        rectangle: np.ndarray
            The rectangle of selected cells. Creates a minimum rectangle
            around all selected cells and is True if the cell is selected.
        start_index: (int, int)
            The start index of the selection. Used to determine the location
            of the copied data.
        """
        copied_data = ""
        for row in range(rectangle.shape[0]):
            for col in range(rectangle.shape[1]):
                if rectangle[row, col]:
                    copied_data += self.data(
                        self.index(start_index[0] + row, start_index[1] + col),
                        Qt.DisplayRole
                    )
                else:
                    copied_data += "SKIP"
                if col < rectangle.shape[1] - 1:
                    copied_data += "\t"
            copied_data += "\n"
        mime_data = QMimeData()
        mime_data.setText(copied_data.strip())
        return mime_data

    def setDataFromText(self, text, start_row, start_column):
        """Set the data from text."""
        # TODO: Does this need to be more flexible in the separator?
        lines = text.split("\n")
        self.maybe_add_rows(start_row, len(lines))
        for row_offset, line in enumerate(lines):
            values = line.split("\t")
            for col_offset, value in enumerate(values):
                if value == "SKIP":
                    continue
                self.setData(
                    self.index(
                        start_row + row_offset, start_column + col_offset
                    ),
                    value,
                    Qt.EditRole
                )

    def maybe_add_rows(self, start_row, n_rows):
        """Add rows if needed."""
        if start_row + n_rows > self._data_frame.shape[0]:
            self.insertRows(
                self._data_frame.shape[0],
                start_row + n_rows - self._data_frame.shape[0]
            )

    def determine_background_color(self, row, column):
        """Determine the background color of a cell.

        1. If it is the first column and last row, return light green.
        2. If it is an invalid cell, return red
        3. If it is an even row return light blue
        4. Otherwise return light green
        """
        if (row, column) == (self._data_frame.shape[0], 0):
            return QColor(144, 238, 144, 150)
        if (row, column) in self.highlighted_cells:
            return QApplication.palette().color(QPalette.Highlight)
        if (row, column) in self._invalid_cells:
            return QColor(255, 100, 100, 150)
        if row % 2 == 0:
            return QColor(144, 190, 109, 102)
        return QColor(177, 217, 231, 102)

    def allow_column_deletion(self, column: int) -> bool:
        """Checks whether the column can safely be deleted"""
        if column == 0 and self._has_named_index:
            return False, self._data_frame.index.name
        column_name = self._data_frame.columns[column-self.column_offset]
        if column_name not in self._allowed_columns.keys():
            return True, column_name
        return self._allowed_columns[column_name]["optional"], column_name

    def endResetModel(self):
        """Override endResetModel to reset the default handler."""
        super().endResetModel()
        self.config = settings_manager.get_table_defaults(self.table_type)
        self.default_handler = DefaultHandlerModel(self, self.config)

    def fill_row(self, row_position: int, data: dict):
        """Fill a row with data.

        Parameters
        ----------
        row_position:
            The position of the row to fill.
        data:
            The data to fill the row with. Gets updated with default values.
        """
        # TODO: Needs undo command, needs syncing with other commands
        # TODO: When undoing a lne and adding then meas -> add both lines
        data_to_add = {
            column_name: "" for column_name in self._data_frame.columns
        }
        unknown_keys = set(data) - set(self._data_frame.columns)
        for key in unknown_keys:
            if key == self._data_frame.index.name:
                continue
            data.pop(key, None)
        data_to_add.update(data)
        index_key = None
        if self.table_type == "condition":
            index_key = data_to_add.pop("conditionId")
        elif self.table_type == "observable":
            index_key = data_to_add.pop("observableId")
        if index_key and self._has_named_index:
            self.undo_stack.push(RenameIndexCommand(
                self, self._data_frame.index.tolist()[row_position],
                index_key, self.index(row_position, 0)
            ))

        changes = {
            (index_key, col): (self._data_frame.at[index_key, col], val)
            for col, val in data_to_add.items()
        }
        self.undo_stack.push(ModifyDataFrameCommand(
            self, changes, "Fill values"
        ))
        self.fill_defaults.emit(self.index(row_position, 0))


class IndexedPandasTableModel(PandasTableModel):
    """Table model for tables with named index."""
    condition_2be_renamed = Signal(str, str)  # Signal to mother controller

    def __init__(self, data_frame, allowed_columns, table_type, parent=None):
        super().__init__(
            data_frame=data_frame,
            allowed_columns=allowed_columns,
            table_type=table_type,
            parent=parent
        )
        self._has_named_index = True
        self.column_offset = 1

    def get_default_values(self, index):
        """Return the default values for a the row in a new index."""
        row_idx = index.row()
        df = self._data_frame
        if isinstance(row_idx, int):
            row_key = df.index[row_idx]
        else:
            row_key = row_idx
        changes = {}
        rename_needed = False
        old_index = row_key
        new_index = row_key

        columns_with_index = [df.index.name] if df.index.name else []
        columns_with_index += list(df.columns)

        for colname in columns_with_index:
            if colname == df.index.name:
                # Generate default index name if empty
                default_value = self.default_handler.get_default(colname, row_key)
                if (
                    not row_key
                    or f"new_{self.table_type}" in row_key
                ):
                    rename_needed = True
                    new_index = default_value
            else:
                if df.at[row_key, colname] == "":
                    default_value = self.default_handler.get_default(colname, row_key)
                    changes[(row_key, colname)] = ("", default_value)

        commands = []
        if changes:
            commands.append(ModifyDataFrameCommand(
                self, changes, "Fill default values"
            ))
        if rename_needed:
            commands.append(RenameIndexCommand(
                self, old_index, new_index, index
            ))
        if not commands:
            return
        if not self.undo_stack:
            for command in commands:
                command.redo()
            return
        self.undo_stack.beginMacro("Fill default values")
        for command in commands:
            self.undo_stack.push(command)
        self.undo_stack.endMacro()

    def handle_named_index(self, index, value):
        """Handle the named index column."""
        row, column = index.row(), index.column()
        old_value = self._data_frame.index[row]
        if value == old_value:
            return False
        if value in self._data_frame.index:
            self.new_log_message.emit(
                f"Duplicate index value '{value}'",
                "red"
            )
            return False
        try:
            self.undo_stack.push(RenameIndexCommand(
                self, old_value, value, index
            ))
            self.relevant_id_changed.emit(value, old_value, self.table_type)
            self.cell_needs_validation.emit(row, 0)
            self.something_changed.emit(True)
            return True
        except Exception as e:
            self.new_log_message.emit(
                f"Error renaming index value '{old_value}' to '{value}': {e}",
                "red"
            )
            return False

    def return_column_index(self, column_name):
        """Return the index of a column."""
        if column_name in self._data_frame.columns:
            return self._data_frame.columns.get_loc(column_name) + 1
        if column_name == self._data_frame.index.name:
            return 0
        return -1


class MeasurementModel(PandasTableModel):
    """Table model for the measurement data."""
    possibly_new_condition = Signal(str)  # Signal for new condition
    possibly_new_observable = Signal(str)  # Signal for new observable

    def __init__(self, data_frame, parent=None):
        super().__init__(
            data_frame=data_frame,
            allowed_columns=COLUMNS["measurement"],
            table_type="measurement",
            parent=parent
        )

    def get_default_values(self, index):
        """Fill missing values in a row without modifying the index."""
        row = index.row()
        df = self._data_frame
        if isinstance(row, int):
            row_key = self._data_frame.index[row]
        else:
            row_key = row

        changes = {}
        for colname in df.columns:
            if df.at[row_key, colname] == "":
                default = self.default_handler.get_default(colname, row_key)
                changes[(row_key, colname)] = ("", default)
        command = ModifyDataFrameCommand(
            self, changes, "Fill default values"
        )
        if self.undo_stack:
            self.undo_stack.push(command)
        else:
            command.redo()

    def data(self, index, role=Qt.DisplayRole):
        """Return the data at the given index and role for the View."""
        if not index.isValid():
            return None
        row, column = index.row(), index.column()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if row == self._data_frame.shape[0]:
                if column == 0:
                    return f"New {self.table_type}"
                return ""
            value = self._data_frame.iloc[row, column]
            if is_invalid(value):
                return ""
            return str(value)
        elif role == Qt.BackgroundRole:
            return self.determine_background_color(row, column)
        elif role == Qt.ForegroundRole:
            # Return yellow text if this cell is a match
            if (row, column) in self.highlighted_cells:
                return QApplication.palette().color(QPalette.HighlightedText)
            return QBrush(QColor(0, 0, 0))  # Default black text
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return the header data for the given section, orientation"""
        if role != Qt.DisplayRole:
            return None
        # role == Qt.DisplayRole
        if orientation == Qt.Horizontal:
            return self._data_frame.columns[section]
        if orientation == Qt.Vertical:
            return str(section)
        return None

    def return_column_index(self, column_name):
        """Return the index of a column."""
        if column_name in self._data_frame.columns:
            return self._data_frame.columns.get_loc(column_name)
        return -1


class ObservableModel(IndexedPandasTableModel):
    """Table model for the observable data."""

    def __init__(self, data_frame, parent=None):
        super().__init__(
            data_frame=data_frame,
            allowed_columns=COLUMNS["observable"],
            table_type="observable",
            parent=parent
        )


class ParameterModel(IndexedPandasTableModel):
    """Table model for the parameter data."""

    def __init__(self, data_frame, parent=None):
        super().__init__(
            data_frame=data_frame,
            allowed_columns=COLUMNS["parameter"],
            table_type="parameter",
            parent=parent
        )


class ConditionModel(IndexedPandasTableModel):
    """Table model for the condition data."""

    def __init__(self, data_frame, parent=None):
        super().__init__(
            data_frame=data_frame,
            allowed_columns=COLUMNS["condition"],
            table_type="condition",
            parent=parent
        )
        self._allowed_columns.pop("conditionId")


class PandasTableFilterProxy(QSortFilterProxyModel):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.source_model = model
        self.setSourceModel(model)

    def filterAcceptsRow(self, source_row, source_parent):
        """Custom filtering logic to apply global filtering across all columns."""
        source_model = self.sourceModel()

        # Always accept the last row (for "add new row")
        if source_row == source_model.rowCount() - 1:
            return True

        regex = self.filterRegularExpression()
        if regex.pattern() == "":
            return True

        for column in range(source_model.columnCount()):
            index = source_model.index(source_row, column, QModelIndex())
            data_str = str(source_model.data(index) or "")
            if regex.match(data_str).hasMatch():
                return True
        return False  # No match found

    def mimeData(self, rectangle, start_index):
        """Return the data to be copied to the clipboard."""
        return self.source_model.mimeData(rectangle, start_index)

    def setDataFromText(self, text, start_row, start_column):
        """Set the data from text."""
        return self.source_model.setDataFromText(text, start_row, start_column)

    @property
    def _invalid_cells(self):
        return self.source_model._invalid_cells
