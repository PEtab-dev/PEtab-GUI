from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QTableView, QWidget,\
    QCompleter, QLineEdit, QStyledItemDelegate, QComboBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from ..utils import get_selected, get_selected_rectangles
from ..C import INDEX


class TableViewer(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.title = title
        self.setObjectName(title)
        self.setAllowedAreas(
            Qt.AllDockWidgetAreas
        )
        widget = QWidget()
        self.setWidget(widget)
        layout = QVBoxLayout(widget)

        # Create the QTableView for the table content
        self.table_view = QTableView()
        layout.addWidget(self.table_view)
        # Dictionary to store column-specific completers
        self.completers = {}

    def copy_to_clipboard(self):
        selected_rect, rect_start = get_selected_rectangles(
            self.table_view
        )
        if selected_rect.any():
            mime_data = self.table_view.model().mimeData(
                selected_rect, rect_start
            )
            clipboard = QGuiApplication.clipboard()
            clipboard.setMimeData(mime_data)

    def paste_from_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()
        if not text:
            return
        start_index = self.table_view.selectionModel().currentIndex()
        if not start_index.isValid():
            return
        model = self.table_view.model()
        row_start, col_start = start_index.row(), start_index.column()
        # identify which invalid cells are being pasted into
        pasted_data = [line.split("\t") for line in text.split("\n") if line.strip()]
        num_rows = len(pasted_data)
        num_cols = max([len(line) for line in pasted_data])
        overridden_cells = {
            (row_start + r, col_start + c)
            for r in range(num_rows)
            for c in range(num_cols)
            if model.index(row_start + r, col_start + c).isValid()
        }
        invalid_overridden_cells = overridden_cells.intersection(
            model._invalid_cells
        )
        if invalid_overridden_cells:
            for row_invalid, col_invalid in invalid_overridden_cells:
                model.discard_invalid_cell(row_invalid, col_invalid)

        model.setDataFromText(
            text, start_index.row(),
            start_index.column()
        )


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.options = options

    def createEditor(self, parent, option, index):
        # Create a QComboBox for inline editing
        editor = QComboBox(parent)
        editor.addItems(self.options)
        return editor


class SingleSuggestionDelegate(QStyledItemDelegate):
    """Suggest a single option based the current row and the value in
    `column_name`."""
    def __init__(self, model, suggestions_column, afix=None, parent=None):
        super().__init__(parent)
        self.model = model  # The main model to retrieve data from
        self.suggestions_column = suggestions_column
        self.afix = afix

    def createEditor(self, parent, option, index):
        # Create a QLineEdit for inline editing
        editor = QLineEdit(parent)

        # Get the conditionId of the current row
        row = index.row()
        suggestion = self.model.get_value_from_column(
            self.suggestions_column, row
        )
        if self.afix:
            suggestion = self.afix + suggestion

        # Set up the completer with a single suggestion
        completer = QCompleter([suggestion], parent)
        completer.setCompletionMode(QCompleter.InlineCompletion)
        editor.setCompleter(completer)

        return editor

class ColumnSuggestionDelegate(QStyledItemDelegate):
    """Suggest options based on all unique values in the specified column."""
    def __init__(
        self,
        model,
        suggestions_column,
        suggestion_mode=QCompleter.PopupCompletion,
        parent=None
    ):
        super().__init__(parent)
        self.model = model  # The main model to retrieve data from
        self.suggestions_column = suggestions_column
        self.suggestion_mode = suggestion_mode

    def createEditor(self, parent, option, index):
        # Create a QLineEdit for inline editing
        editor = QLineEdit(parent)

        # Get unique suggestions from the specified column
        suggestions = self.model.unique_values(self.suggestions_column)

        # Set up the completer with the unique values
        completer = QCompleter(suggestions, parent)
        completer.setCompletionMode(self.suggestion_mode)
        editor.setCompleter(completer)

        return editor


class ParameterIdSuggestionDelegate(QStyledItemDelegate):
    """Suggest options based on all unique values in the specified column."""
    def __init__(self, par_model, sbml_model, parent=None):
        super().__init__(parent)
        self.par_model = par_model
        self.sbml_model = sbml_model  # The main model to retrieve data from

    def createEditor(self, parent, option, index):
        # Create a QLineEdit for inline editing
        editor = QLineEdit(parent)

        # Get unique suggestions from the specified column
        curr_model = self.sbml_model.get_current_sbml_model()
        suggestions = None
        if curr_model:  # only if model is valid
            suggestions = curr_model.get_valid_parameters_for_parameter_table()
            # substract the current parameter ids except for the current row
            row = index.row()
            selected_parameter_id = self.par_model.get_value_from_column(
                'parameterId', row
            )
            current_parameter_ids = self.par_model.get_df().index.tolist()
            if selected_parameter_id in current_parameter_ids:
                current_parameter_ids.remove(selected_parameter_id)
            suggestions = list(set(suggestions) - set(current_parameter_ids))

        # Set up the completer with the unique values
        completer = QCompleter(suggestions, parent)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        editor.setCompleter(completer)

        return editor
