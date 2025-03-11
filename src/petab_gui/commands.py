"""Store commands for the do/undo functionality."""
import copy
from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QModelIndex


class ModifyColumnCommand(QUndoCommand):
    """Command to add a column to the table."""

    def __init__(self, model, column_name, add_mode: bool = True):
        action = "Add" if add_mode else "Remove"
        super().__init__(
            f"{action} column {column_name} in table {model.table_type}"
        )
        self.model = model
        self.column_name = column_name
        self.add_mode = add_mode
        self.old_values = None
        if not add_mode and column_name in model._data_frame.columns:
            self.old_values = model._data_frame[column_name].copy()

    def redo(self):
        if self.add_mode:
            position = self.model._data_frame.shape[1]
            self.model.beginInsertColumns(
                QModelIndex(), position, position
            )
            self.model._data_frame[self.column_name] = ""
            self.model.endInsertColumns()
        else:
            position = list(
                self.model._data_frame.columns
            ).index(self.column_name)
            self.model.beginRemoveColumns(
                QModelIndex(), position, position
            )
            self.model._data_frame.drop(columns=self.column_name, inplace=True)
            self.model.endRemoveColumns()

    def undo(self):
        if self.add_mode:
            position = list(
                self.model._data_frame.columns
            ).index(self.column_name)
            self.model.beginRemoveColumns(
                QModelIndex(), position, position
            )
            self.model._data_frame.drop(columns=self.column_name, inplace=True)
            self.model.endRemoveColumns()
        else:
            position = self.model._data_frame.shape[1]
            self.model.beginInsertColumns(
                QModelIndex(), position, position
            )
            self.model._data_frame[self.column_name] = self.old_values
            self.model.endInsertColumns()
        self.model.beginRemoveColumns(
            QModelIndex(), position, position
        )
