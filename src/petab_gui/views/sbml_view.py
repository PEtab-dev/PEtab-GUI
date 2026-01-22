"""Widget for viewing the SBML model."""

import qtawesome as qta
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

        # Reference to menu action (set by controller)
        self.sbml_toggle_action = None
        self.save_sbml_action = None

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
        # Enable custom context menu
        self.sbml_text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sbml_text_edit.customContextMenuRequested.connect(
            self._show_sbml_context_menu
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
        # Enable custom context menu
        self.antimony_text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.antimony_text_edit.customContextMenuRequested.connect(
            self._show_antimony_context_menu
        )
        antimony_layout.addWidget(self.antimony_text_edit)

        # Add forward changes button for Antimony
        self.forward_antimony_button = QPushButton("Forward Changes to SBML")
        antimony_layout.addWidget(self.forward_antimony_button)

        # Create widgets to hold SBML and Antimony sections
        self.sbml_widget = QWidget()
        self.sbml_widget.setLayout(sbml_layout)

        antimony_widget = QWidget()
        antimony_widget.setLayout(antimony_layout)

        # Add widgets to the splitter
        splitter.addWidget(self.sbml_widget)
        splitter.addWidget(antimony_widget)

        # Add the splitter to the main layout
        vertical_splitter.addWidget(splitter)
        if logger_view:
            vertical_splitter.addWidget(logger_view)
        layout.addWidget(vertical_splitter)
        vertical_splitter.setStretchFactor(0, 7)
        vertical_splitter.setStretchFactor(1, 3)

    def _show_sbml_context_menu(self, position):
        """Show context menu for SBML text edit."""
        if not self.sbml_toggle_action:
            return

        menu = self.sbml_text_edit.createStandardContextMenu()
        menu.addSeparator()

        # Add export SBML option
        if self.save_sbml_action:
            menu.addAction(self.save_sbml_action)
            menu.addSeparator()

        # Add hide SBML option
        hide_action = menu.addAction(
            qta.icon("mdi6.chevron-left"), "Hide SBML Editor"
        )
        hide_action.triggered.connect(
            lambda: self.sbml_toggle_action.setChecked(False)
        )

        menu.exec(self.sbml_text_edit.mapToGlobal(position))

    def _show_antimony_context_menu(self, position):
        """Show context menu for Antimony text edit."""
        if not self.sbml_toggle_action:
            return

        menu = self.antimony_text_edit.createStandardContextMenu()
        menu.addSeparator()

        # Add export SBML option
        if self.save_sbml_action:
            menu.addAction(self.save_sbml_action)
            menu.addSeparator()

        # Add show/hide SBML option
        if self.sbml_widget.isVisible():
            action = menu.addAction(
                qta.icon("mdi6.chevron-left"), "Hide SBML Editor"
            )
            action.triggered.connect(
                lambda: self.sbml_toggle_action.setChecked(False)
            )
        else:
            action = menu.addAction(
                qta.icon("mdi6.chevron-right"), "Show SBML Editor"
            )
            action.triggered.connect(
                lambda: self.sbml_toggle_action.setChecked(True)
            )

        menu.exec(self.antimony_text_edit.mapToGlobal(position))
