import functools
import html
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import petab.v1 as petab
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QTabBar,
    QToolButton,
    QWhatsThis,
)

from ..C import COMMON_ERRORS
from ..settings_manager import settings_manager


class _WhatsThisClickHelp(QObject):
    """Global filter to show a What's This bubble on left-click while the action is checked.

    Behavior:
      • Left-click: show help for the widget under the cursor.
      • Works for generic widgets via widget.whatsThis() → widget.toolTip().
      • Special handling for QTabBar: shows per-tab help using tabToolTip/tabText.
      • ESC: exit help mode (uncheck action) and hide any open bubble.
    """

    def __init__(self, action):
        super().__init__()
        self.action = action

    def eventFilter(self, _obj, ev):
        # Ignore everything if help mode toggle is off.
        if not self.action.isChecked():
            return False

        # ESC closes bubble and exits help mode.
        if ev.type() == QEvent.KeyPress and ev.key() == Qt.Key_Escape:
            self.action.blockSignals(True)
            self.action.setChecked(False)
            self.action.blockSignals(False)
            QWhatsThis.hideText()
            return True  # consume ESC

        # Left-click: show the appropriate What's This bubble.
        if ev.type() == QEvent.MouseButtonPress and (ev.buttons() & Qt.LeftButton):
            QWhatsThis.hideText()  # close any previous bubble

            w = QApplication.widgetAt(QCursor.pos())
            if not w:
                return True  # consume click in help mode even if no widget
            # If the user clicks the "What's This" toolbar button while in help mode,
            # exit help mode immediately (close bubble, uncheck action, remove filter).
            if isinstance(w, QToolButton) and w.defaultAction() is self.action:
                self.action.blockSignals(True)
                self.action.setChecked(False)
                self.action.blockSignals(False)
                QWhatsThis.hideText()
                app = QApplication.instance()
                if app:
                        app.removeEventFilter(self)
                return True

            # --- Special case: tab bars (clicking tabs) ---
            if isinstance(w, QTabBar):
                local_pos = w.mapFromGlobal(QCursor.pos())
                i = w.tabAt(local_pos)
                if i != -1:
                    # Prefer tab-specific tooltip; fall back to tab text.
                    text = w.tabToolTip(i) or w.tabText(i) or "No help available."
                    # Anchor the bubble to the tab's rect for better placement.
                    QWhatsThis.showText(QCursor.pos(), text, w)
                    return True  # consume: don't switch tabs while in help mode

            # --- Generic widgets: try what'sThis(), then toolTip() ---
            text = w.whatsThis() or w.toolTip() or "No help available."
            QWhatsThis.showText(QCursor.pos(), text, w)
            return True  # consume click

        return False  # let other events pass


def linter_wrapper(_func=None, additional_error_check: bool = False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(
            self,
            row_data: pd.DataFrame = None,
            row_name: str = None,
            col_name: str = None,
            *args,
            **kwargs,
        ):
            try:
                func(self, row_data, row_name, col_name, *args, **kwargs)
                return True
            except Exception as e:
                err_msg = filtered_error(e)
                err_msg = html.escape(err_msg)
                if (additional_error_check and "Missing parameter(s)" in
                    err_msg):
                        match = re.search(r"\{(.+?)}", err_msg)
                        missing_params = {
                            s.strip(" '") for s in match.group(1).split(",")
                        }
                        remain = {
                            p
                            for p in missing_params
                            if p not in self.model._data_frame.index
                        }
                        if not remain:
                            return True
                        err_msg = re.sub(
                            r"\{.*?}",
                            "{" + ", ".join(sorted(remain)) + "}",
                            err_msg,
                        )
                msg = "PEtab linter failed"
                if row_name is not None and col_name is not None:
                    msg = f"{msg} at ({row_name}, {col_name}): {err_msg}"
                else:
                    msg = f"{msg}: {err_msg}"

                self.logger.log_message(msg, color="red")
                return False

        return wrapper

    if callable(_func):  # used without parentheses
        return decorator(_func)
    return decorator


def filtered_error(error_message: BaseException) -> str:
    """Filters know error message and reformulates them."""
    all_errors = "|".join(
        f"(?P<key{i}>{pattern})" for i, pattern in enumerate(COMMON_ERRORS)
    )
    regex = re.compile(all_errors)
    replacement_values = list(COMMON_ERRORS.values())

    # Replace function
    def replacer(match):
        for i, _ in enumerate(COMMON_ERRORS):
            if match.group(f"key{i}"):
                return replacement_values[i]
        return match.group(0)

    return regex.sub(replacer, str(error_message))


def prompt_overwrite_or_append(controller):
    """Prompt user to choose between overwriting or appending the file."""
    msg_box = QMessageBox(controller.view)
    msg_box.setWindowTitle("Open File Options")
    msg_box.setText(
        "Do you want to overwrite the current data or append to it?"
    )
    overwrite_button = msg_box.addButton("Overwrite", QMessageBox.AcceptRole)
    append_button = msg_box.addButton("Append", QMessageBox.AcceptRole)
    cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

    msg_box.exec()

    if msg_box.clickedButton() == cancel_button:
        return None
    if msg_box.clickedButton() == overwrite_button:
        return "overwrite"
    if msg_box.clickedButton() == append_button:
        return "append"
    return None


class RecentFilesManager(QObject):
    """Manage a list of recent files."""

    open_file = Signal(str)  # Signal to open a file

    def __init__(self, max_files=10):
        super().__init__()
        self.max_files = max_files
        self.recent_files = self.load_recent_files()
        self.tool_bar_menu = QMenu("Recent Files")
        self.update_tool_bar_menu()

    def add_file(self, file_path):
        """Add a file to the recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[: self.max_files]
        self.save_recent_files()
        self.update_tool_bar_menu()

    @staticmethod
    def load_recent_files():
        """Load recent files from settings."""
        return settings_manager.get_value("recent_files", [])

    def save_recent_files(self):
        """Save recent files to settings."""
        settings_manager.set_value("recent_files", self.recent_files)

    def update_tool_bar_menu(self):
        """Update the recent files menu."""
        self.tool_bar_menu.clear()

        # Generate shortened names
        def short_name(path):
            p = Path(path)
            if p.parent.name:
                return f"{p.parent.name}/{p.name}"
            return p.name

        short_paths = [short_name(f) for f in self.recent_files]
        counts = Counter(short_paths)

        for full_path, short in zip(
            self.recent_files, short_paths, strict=False
        ):
            display = full_path if counts[short] > 1 else short
            action = QAction(display, self.tool_bar_menu)
            action.triggered.connect(
                lambda _, p=full_path: self.open_file.emit(p)
            )
            self.tool_bar_menu.addAction(action)
        self.tool_bar_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self.tool_bar_menu)
        clear_action.triggered.connect(self.clear_recent_files)

    def clear_recent_files(self):
        """Clear the recent files list."""
        self.recent_files = []
        self.save_recent_files()
        self.update_tool_bar_menu()

def save_petab_table(
    df: pd.DataFrame, filename: str | Path, table_type: str
):
    """Save a PEtab table to a file. Function used based on table type."""
    if table_type == "condition":
        petab.write_condition_df(df, filename)
    elif table_type in ["measurement", "simulation"]:
        petab.write_measurement_df(df, filename)
    elif table_type == "parameter":
        petab.write_parameter_df(df, filename)
    elif table_type == "observable":
        petab.write_observable_df(df, filename)
    else:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filename, sep="\t", index=False)
