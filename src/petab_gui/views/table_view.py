from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QTableView, QWidget
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
