"""Store commands for the do/undo functionality."""
import copy
from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QModelIndex


class AddColumnCommand(QUndoCommand):
    """Command to add a column to the table."""

    def __init__(self, model, column_name):
        super().__init__(
            f"Add column {column_name} in table {model.table_type}"
        )
        self.model = model
        self.column_name = column_name
        self.position = copy.deepcopy(self.model.get_df().shape[1])
        self.was_added = False

    def redo(self):
        self.model.beginInsertColumns(
            QModelIndex(), self.position, self.position
        )
        self.model._data_frame[self.column_name] = ""
        self.model.endInsertColumns()
        self.was_added = True

    def undo(self):
        self.model.beginRemoveColumns(
            QModelIndex(), self.position, self.position
        )
        self.model._data_frame.drop(columns=self.column_name, inplace=True)
        self.model.endRemoveColumns()
        self.was_added = False
