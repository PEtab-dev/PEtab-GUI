"""File containing the logger widget.

Contains logger widget as well as two helper buttons.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QTextBrowser, QWidget


class Logger(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create the logger (QTextBrowser)
        self.logger = QTextBrowser(parent)

        self.logger.setOpenExternalLinks(True)
        self.logger.setTextInteractionFlags(Qt.TextBrowserInteraction)

        # Create the main layout for Logger
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.logger)
