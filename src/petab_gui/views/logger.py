"""File containing the logger widget.

Contains logger widget as well as two helper buttons.
"""
from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QHBoxLayout, \
    QPushButton, QWidget


class Logger(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create buttons
        self.upload_data_matrix_button = QPushButton("Add Data Matrix",
                                                     parent)
        self.reset_to_original_button = QPushButton("Reset to Original Model",
                                                    parent)
        self.lint_model_button = QPushButton("Check Model", parent)

        # Hide the reset button initially
        self.reset_to_original_button.hide()

        # Ensure buttons have the same size
        button_size = self.reset_to_original_button.sizeHint()
        self.upload_data_matrix_button.setMinimumSize(button_size)
        self.lint_model_button.setMinimumSize(button_size)
        self.reset_to_original_button.setMinimumSize(button_size)

        # Create the logger (QTextBrowser)
        self.logger = QTextBrowser(parent)

        # Layout for the buttons
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.upload_data_matrix_button)
        button_layout.addWidget(self.reset_to_original_button)
        button_layout.addWidget(self.lint_model_button)

        # Create the main layout for Logger
        main_layout = QHBoxLayout(self)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.logger)
