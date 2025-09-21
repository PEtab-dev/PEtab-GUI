"""Widget for viewing the SBML model."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..models.tooltips import ANTIMONY_VIEW_TOOLTIP, SBML_VIEW_TOOLTIP
from .whats_this import WHATS_THIS


class SbmlViewer(QWidget):
    """Widget for viewing the SBML model."""

    def __init__(self, parent=None, logger_view=None):
        super().__init__(parent)

        # Main layout for the SBML tab
        layout = QVBoxLayout(self)
        vertical_splitter = QSplitter(Qt.Vertical)

        # Create splitter to divide the SBML and Antimony sections
        splitter = QSplitter(Qt.Horizontal)

        # Create SBML model section
        sbml_layout = QVBoxLayout()
        sbml_label = QLabel("SBML Model")
        sbml_layout.addWidget(sbml_label)
        self.sbml_text_edit = QPlainTextEdit()
        self.sbml_text_edit.setToolTip(SBML_VIEW_TOOLTIP)
        self.sbml_text_edit.setWhatsThis(
            WHATS_THIS["sbml_view"]["sbml_editor"]
        )
        sbml_layout.addWidget(self.sbml_text_edit)

        # Add forward changes button for SBML
        self.forward_sbml_button = QPushButton("Forward Changes to Antimony")
        sbml_layout.addWidget(self.forward_sbml_button)

        # Create Antimony model section
        antimony_layout = QVBoxLayout()
        antimony_label = QLabel("Antimony Model")
        antimony_layout.addWidget(antimony_label)
        self.antimony_text_edit = QPlainTextEdit()
        self.antimony_text_edit.setToolTip(ANTIMONY_VIEW_TOOLTIP)
        self.sbml_text_edit.setWhatsThis(
            WHATS_THIS["sbml_view"]["antimony_editor"]
        )
        antimony_layout.addWidget(self.antimony_text_edit)

        # Add forward changes button for Antimony
        self.forward_antimony_button = QPushButton("Forward Changes to SBML")
        antimony_layout.addWidget(self.forward_antimony_button)

        # Create widgets to hold SBML and Antimony sections
        sbml_widget = QWidget()
        sbml_widget.setLayout(sbml_layout)

        antimony_widget = QWidget()
        antimony_widget.setLayout(antimony_layout)

        # Add widgets to the splitter
        splitter.addWidget(sbml_widget)
        splitter.addWidget(antimony_widget)

        # Add the splitter to the main layout
        vertical_splitter.addWidget(splitter)
        if logger_view:
            vertical_splitter.addWidget(logger_view)
        layout.addWidget(vertical_splitter)
        vertical_splitter.setStretchFactor(0, 7)
        vertical_splitter.setStretchFactor(1, 3)
