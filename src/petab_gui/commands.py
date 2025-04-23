"""Store commands for the do/undo functionality."""
from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QModelIndex, Qt
import pandas as pd


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
        self.position = None

        if not add_mode and column_name in model._data_frame.columns:
            self.position = model._data_frame.columns.get_loc(column_name)
            self.old_values = model._data_frame[column_name].copy()

    def redo(self):
        if self.add_mode:
            position = self.model._data_frame.shape[1]
            self.model.beginInsertColumns(QModelIndex(), position, position)
            self.model._data_frame[self.column_name] = ""
            self.model.endInsertColumns()
        else:
            self.position = self.model._data_frame.columns.get_loc(self.column_name)
            self.model.beginRemoveColumns(QModelIndex(), self.position, self.position)
            self.model._data_frame.drop(columns=self.column_name, inplace=True)
            self.model.endRemoveColumns()

    def undo(self):
        if self.add_mode:
            position = self.model._data_frame.columns.get_loc(self.column_name)
            self.model.beginRemoveColumns(QModelIndex(), position, position)
            self.model._data_frame.drop(columns=self.column_name, inplace=True)
            self.model.endRemoveColumns()
        else:
            self.model.beginInsertColumns(QModelIndex(), self.position, self.position)
            self.model._data_frame.insert(self.position, self.column_name, self.old_values)
            self.model.endInsertColumns()


class ModifyRowCommand(QUndoCommand):
    """Command to add a row to the table."""

    def __init__(
        self,
        model,
        row_indices: list[int] | int,
        add_mode: bool = True
    ):
        action = "Add" if add_mode else "Remove"
        super().__init__(f"{action} row(s) in table {model.table_type}")
        self.model = model
        self.add_mode = add_mode
        self.old_rows = None
        self.old_ind_names = None

        df = self.model._data_frame

        if add_mode:
            # Adding: interpret input as count of new rows
            self.row_indices = self._generate_new_indices(row_indices)
        else:
            # Deleting: interpret input as specific index labels
            self.row_indices = row_indices if isinstance(row_indices, list) else [row_indices]
            self.old_rows = df.iloc[self.row_indices].copy()
            self.old_ind_names = [df.index[idx] for idx in self.row_indices]

    def _generate_new_indices(self, count):
        """Generate default row indices based on table type and index type."""
        df = self.model._data_frame
        base = 0
        existing = set(df.index.astype(str))

        indices = []
        while len(indices) < count:
            idx = f"new_{self.model.table_type}_{base}"
            if idx not in existing:
                indices.append(idx)
            base += 1
        self.old_ind_names = indices
        return indices

    def redo(self):
        df = self.model._data_frame

        if self.add_mode:
            position = df.shape[0] - 1  # insert *before* the auto-row
            self.model.beginInsertRows(QModelIndex(), position, position + len(self.row_indices) - 1)
            for i, idx in enumerate(self.row_indices):
                df.loc[idx] = [""] * df.shape[1]
            self.model.endInsertRows()
        else:
            self.model.beginRemoveRows(QModelIndex(), min(self.row_indices), max(self.row_indices))
            df.drop(index=self.old_ind_names, inplace=True)
            self.model.endRemoveRows()

    def undo(self):
        df = self.model._data_frame

        if self.add_mode:
            positions = [df.index.get_loc(idx) for idx in self.row_indices]
            self.model.beginRemoveRows(QModelIndex(), min(positions), max(positions))
            df.drop(index=self.old_ind_names, inplace=True)
            self.model.endRemoveRows()
        else:
            self.model.beginInsertRows(QModelIndex(), min(self.row_indices), max(self.row_indices))
            restore_index_order = df.index
            for pos, index_name, row in zip(
                self.row_indices, self.old_ind_names, self.old_rows.values
            ):
                restore_index_order = restore_index_order.insert(
                    pos, index_name
                )
                df.loc[index_name] = row
                df.sort_index(
                    inplace=True,
                    key=lambda x: x.map(restore_index_order.get_loc)
                )
            self.model.endInsertRows()


class ModifyDataFrameCommand(QUndoCommand):
    def __init__(self, model, changes: dict[tuple, tuple], description="Modify values"):
        super().__init__(description)
        self.model = model
        self.changes = changes  # {(row_key, column_name): (old_val, new_val)}

    def redo(self):
        self._apply_changes(use_new=True)

    def undo(self):
        self._apply_changes(use_new=False)

    def _apply_changes(self, use_new: bool):
        df = self.model._data_frame
        col_offset = 1 if self.model._has_named_index else 0

        # Apply changes
        update_vals = {
            (row, col): val[1 if use_new else 0]
            for (row, col), val in self.changes.items()
        }
        update_df = pd.Series(update_vals).unstack()
        update_df.replace({None: "Placeholder_temp"}, inplace=True)
        df.update(update_df)
        df.replace({"Placeholder_temp": ""}, inplace=True)

        rows = [df.index.get_loc(row_key) for (row_key, _) in
                self.changes.keys()]
        cols = [df.columns.get_loc(col) + col_offset for (_, col) in
                self.changes.keys()]

        top_left = self.model.index(min(rows), min(cols))
        bottom_right = self.model.index(max(rows), max(cols))
        self.model.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])


class RenameIndexCommand(QUndoCommand):
    def __init__(self, model, old_index, new_index, model_index):
        super().__init__(f"Rename index {old_index} → {new_index}")
        self.model = model
        self.model_index = model_index
        self.old_index = old_index
        self.new_index = new_index

    def redo(self):
        self._apply(self.old_index, self.new_index)

    def undo(self):
        self._apply(self.new_index, self.old_index)

    def _apply(self, src, dst):
        df = self.model._data_frame
        df.rename(index={src: dst}, inplace=True)
        self.model.dataChanged.emit(
            self.model_index, self.model_index, [Qt.DisplayRole]
        )
