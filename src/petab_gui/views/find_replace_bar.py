import logging
import re

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class FindReplaceBar(QWidget):
    """Find and replace bar widget.

    This widget depends on FindReplaceController to coordinate search
    operations across multiple tables.
    """

    def __init__(self, controller, parent=None):
        """Initialize the find/replace bar.

        Args:
            controller: FindReplaceController for operations across tables
        """
        super().__init__(parent)
        self.controller = controller
        self.selected_table_names = self.controller.get_table_names()
        self.only_search = False
        self.matches = None

        # 🔍 Find Input with options
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        self.find_input.textChanged.connect(self.run_find)

        self.case_sensitive_button = QToolButton()
        self.case_sensitive_button.setIcon(qta.icon("mdi6.format-letter-case"))
        self.case_sensitive_button.setCheckable(True)
        self.case_sensitive_button.toggled.connect(self.run_find)

        self.word_match_button = QToolButton()
        self.word_match_button.setIcon(qta.icon("mdi6.alpha-w"))
        self.word_match_button.setCheckable(True)
        self.word_match_button.toggled.connect(self.run_find)

        self.regex_button = QToolButton()
        self.regex_button.setIcon(qta.icon("mdi6.regex"))
        self.regex_button.setCheckable(True)
        self.regex_button.toggled.connect(self.run_find)

        find_layout = QHBoxLayout()
        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.case_sensitive_button)
        find_layout.addWidget(self.word_match_button)
        find_layout.addWidget(self.regex_button)

        # 🔄 Replace Input
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace...")

        replace_layout = QHBoxLayout()
        replace_layout.addWidget(self.replace_input)

        # 🔘 Action Buttons (Navigation, Results, Replace, Close)
        self.prev_button = QPushButton()
        self.prev_button.setIcon(qta.icon("mdi6.arrow-up"))
        self.next_button = QPushButton()
        self.next_button.setIcon(qta.icon("mdi6.arrow-down"))
        self.prev_button.clicked.connect(self.find_previous)
        self.next_button.clicked.connect(self.find_next)

        self.results_label = QLabel("0 results")
        self.filter_button = QPushButton()
        self.filter_button.setIcon(qta.icon("mdi6.filter"))
        self.close_button = QPushButton()
        self.filter_button.clicked.connect(self.show_filter_menu)
        self.filter_menu = QMenu(self)  # Dropdown menu
        self.filter_actions = {}
        self._build_filter_menu()
        self.close_button.setIcon(qta.icon("mdi6.close"))
        self.close_button.clicked.connect(self.hide)

        self.replace_button = QPushButton("Replace")
        self.replace_button.clicked.connect(self.replace_current_match)
        self.replace_all_button = QPushButton("Replace All")
        self.replace_all_button.clicked.connect(self.replace_all)

        find_controls_layout = QHBoxLayout()
        find_controls_layout.addWidget(self.results_label)
        find_controls_layout.addWidget(self.prev_button)
        find_controls_layout.addWidget(self.next_button)
        find_controls_layout.addWidget(self.filter_button)
        find_controls_layout.addWidget(self.close_button)

        replace_controls_layout = QHBoxLayout()
        replace_controls_layout.addWidget(self.replace_button)
        replace_controls_layout.addWidget(self.replace_all_button)

        # 🔹 Main Layout
        self.layout_main = QHBoxLayout()
        self.layout_edits = QVBoxLayout()
        self.layout_options = QVBoxLayout()

        self.layout_edits.addLayout(find_layout)
        self.layout_edits.addLayout(replace_layout)

        self.layout_options.addLayout(find_controls_layout)
        self.layout_options.addLayout(replace_controls_layout)

        self.layout_main.addLayout(self.layout_edits)
        self.layout_main.addLayout(self.layout_options)
        self.setLayout(self.layout_main)

    def _build_filter_menu(self):
        """Build the filter menu with checkable actions for each table."""
        # Clear existing actions
        self.filter_menu.clear()
        self.filter_actions.clear()

        # Add "All" option
        action = QAction("All", self.filter_menu)
        action.setCheckable(True)
        action.setChecked(True)
        action.triggered.connect(self.update_selected_tables)
        self.filter_menu.addAction(action)
        self.filter_actions["All"] = action

        # Add action for each table
        for table_name in self.controller.get_table_names():
            action = QAction(table_name, self.filter_menu)
            action.setCheckable(True)
            action.triggered.connect(self.update_selected_tables)
            self.filter_menu.addAction(action)
            self.filter_actions[table_name] = action

    def run_find(self):
        """Triggered when the search text changes."""
        search_text = self.find_input.text()
        if not search_text:
            self.controller.cleanse_all_highlights()
            self.matches = []
            self.current_match_ind = -1
            self.update_result_label()
            return

        case_sensitive = self.case_sensitive_button.isChecked()
        regex = self.regex_button.isChecked()
        whole_cell = self.word_match_button.isChecked()

        # Use controller to find text across selected tables
        self.matches = self.controller.find_text(
            search_text,
            case_sensitive,
            regex,
            whole_cell,
            self.selected_table_names,
        )

        self.current_match_ind = -1
        if self.matches:
            self.current_match_ind = 0
            self.focus_match(self.matches[self.current_match_ind])

        self.update_result_label()

    def find_next(self):
        """Move to the next match."""
        if not self.matches:
            return
        # Unfocus current match
        __, _, table_name, __ = self.matches[self.current_match_ind]
        self.controller.unfocus_match(table_name)

        # Move to next match
        self.current_match_ind = (self.current_match_ind + 1) % len(
            self.matches
        )
        row, col, table_name, __ = self.matches[self.current_match_ind]
        self.controller.focus_match(table_name, row, col, with_focus=True)
        self.update_result_label()

    def find_previous(self):
        """Move to the previous match."""
        if not self.matches:
            return
        # Unfocus current match
        __, _, table_name, __ = self.matches[self.current_match_ind]
        self.controller.unfocus_match(table_name)

        # Move to previous match
        self.current_match_ind = (self.current_match_ind - 1) % len(
            self.matches
        )
        row, col, table_name, __ = self.matches[self.current_match_ind]
        self.controller.focus_match(table_name, row, col, with_focus=True)
        self.update_result_label()

    def update_result_label(self):
        """Update the result label dynamically."""
        match_count = len(self.matches)
        self.results_label.setText(
            f"{self.current_match_ind + 1}/{match_count}"
            if match_count > 0
            else "0 results"
        )

    def replace_current_match(self):
        """Replace the currently selected match and move to the next one."""
        if not self.matches or self.current_match_ind == -1:
            return

        replace_text = self.replace_input.text()
        if not replace_text:
            return

        row, col, table_name, __ = self.matches[self.current_match_ind]

        self.controller.replace_text(
            table_name=table_name,
            row=row,
            col=col,
            replace_text=replace_text,
            search_text=self.find_input.text(),
            case_sensitive=self.case_sensitive_button.isChecked(),
            regex=self.regex_button.isChecked(),
        )

        # Drop the current match and update the result label
        self.matches.pop(self.current_match_ind)
        self.update_result_label()
        match = self.matches[self.current_match_ind] if self.matches else None
        self.focus_match(match, with_focus=True)

    def replace_all(self):
        """Replace all matches with the given text."""
        if not self.matches:
            return

        replace_text = self.replace_input.text()
        search_text = self.find_input.text()
        case_sensitive = self.case_sensitive_button.isChecked()
        regex = self.regex_button.isChecked()

        # Use controller to replace all matches
        self.controller.replace_all(
            search_text, replace_text, case_sensitive, regex, self.matches
        )
        self.controller.cleanse_all_highlights()
        self.run_find()

    def focus_match(self, match, with_focus: bool = False):
        """Focus the match in the correct table."""
        if not match:
            return
        row, col, table_name, __ = match
        self.controller.focus_match(table_name, row, col, with_focus)

    def show_filter_menu(self):
        """Show the filter selection dropdown below the filter button."""
        self.filter_menu.exec_(
            self.filter_button.mapToGlobal(
                self.filter_button.rect().bottomLeft()
            )
        )

    def update_selected_tables(self):
        """Update which tables are included in the search."""
        if self.filter_actions["All"].isChecked():
            self.selected_table_names = self.controller.get_table_names()
        else:
            self.selected_table_names = [
                table_name
                for table_name, action in self.filter_actions.items()
                if action.isChecked() and (table_name != "All")
            ]
        self.run_find()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event: QHideEvent):
        """Reset highlights when the Find/Replace bar is hidden."""
        self.controller.cleanse_all_highlights()
        super().hideEvent(event)

    def showEvent(self, event: QShowEvent):
        """Reset highlights when the Find/Replace bar is shown."""
        if not self.matches:
            super().showEvent(event)
            return
        # Highlight all matches using controller
        self.controller.highlight_matches(self.matches)
        super().showEvent(event)

    def show_replace_parts(self, show: bool = False):
        """Toggle the visibility of the replace parts."""
        self.replace_input.setVisible(show)
        self.replace_button.setVisible(show)
        self.replace_all_button.setVisible(show)

    def toggle_find(self):
        """Toggle behaviour of the search bar."""
        if not self.isVisible():
            self.show()
            self.show_replace_parts(False)
            self.only_search = True
            return
        if not self.only_search:
            self.show_replace_parts(False)
            self.only_search = True
            return
        self.hide()

    def toggle_replace(self):
        """Toggle behaviour of the replace bar."""
        if not self.isVisible():
            self.show()
            self.show_replace_parts(True)
            self.only_search = False
            return
        if self.only_search:
            self.show_replace_parts(True)
            self.only_search = False
            return
        self.hide()
