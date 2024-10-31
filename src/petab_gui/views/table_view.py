from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QTableView, QWidget,\
    QCompleter, QLineEdit, QStyledItemDelegate, QComboBox
from PySide6.QtCore import Qt


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


class InlineCompleterDelegate(QStyledItemDelegate):
    def __init__(self, suggestions, parent=None):
        super().__init__(parent)
        self.suggestions = suggestions

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        completer = QCompleter(self.suggestions, parent)
        completer.setCompletionMode(QCompleter.InlineCompletion)
        editor.setCompleter(completer)
        return editor


class PopupCompleterDelegate(QStyledItemDelegate):
    def __init__(self, suggestions, parent=None):
        super().__init__(parent)
        self.suggestions = suggestions

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        completer = QCompleter(self.suggestions, parent)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        editor.setCompleter(completer)
        return editor


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.options = options

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.options)
        return editor

class SingleSuggestionDelegate(QStyledItemDelegate):
    """Suggest a single option based the current row and the value in
    `column_name`."""
    def __init__(self, model, suggestions_column, parent=None):
        super().__init__(parent)
        self.model = model  # The main model to retrieve data from
        self.suggestions_column = suggestions_column

    def createEditor(self, parent, option, index):
        # Create a QLineEdit for inline editing
        editor = QLineEdit(parent)

        # Get the conditionId of the current row
        row = index.row()
        suggestion = self.model.get_value_from_column(
            self.suggestions_column, row
        )

        # Set up the completer with a single suggestion
        completer = QCompleter([suggestion], parent)
        completer.setCompletionMode(QCompleter.InlineCompletion)
        editor.setCompleter(completer)

        return editor

