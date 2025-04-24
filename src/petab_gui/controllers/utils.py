from PySide6.QtWidgets import QMessageBox, QMenu
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from collections import Counter
from pathlib import Path
import functools
import pandas as pd
import re

from ..settings_manager import settings_manager
from ..C import COMMON_ERRORS


def linter_wrapper(_func=None, additional_error_check: bool = False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, row_data: pd.DataFrame = None, row_name:
                str = None, col_name: str = None, *args, **kwargs):
            try:
                result = func(
                    self, row_data, row_name, col_name, *args, **kwargs
                )
                return True
            except Exception as e:
                err_msg = filtered_error(e)
                if additional_error_check:
                    if "Missing parameter(s)" in err_msg:
                        match = re.search(r"\{(.+?)\}", err_msg)
                        missing_params = {
                            s.strip(" '") for s in match.group(1).split(",")
                        }
                        remain = {
                            p for p in missing_params
                            if p not in self.model._data_frame.index
                        }
                        if not remain:
                            return True
                        err_msg = re.sub(
                            r"\{.*?\}", "{" + ", ".join(sorted(remain)) + "}",
                            err_msg
                        )
                if row_name is not None and col_name is not None:
                    msg = f"PEtab linter failed at ({row_name}, {col_name}): {err_msg}"
                else:
                    msg = f"PEtab linter failed: {err_msg}"

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
    msg_box.setText("Do you want to overwrite the current data or append to it?")
    overwrite_button = msg_box.addButton("Overwrite", QMessageBox.AcceptRole)
    append_button = msg_box.addButton("Append", QMessageBox.AcceptRole)
    cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

    msg_box.exec()

    if msg_box.clickedButton() == cancel_button:
        return None
    elif msg_box.clickedButton() == overwrite_button:
        return "overwrite"
    elif msg_box.clickedButton() == append_button:
        return "append"


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
        self.recent_files = self.recent_files[:self.max_files]
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

        for full_path, short in zip(self.recent_files, short_paths):
            display = full_path if counts[short] > 1 else short
            action = QAction(display, self.tool_bar_menu)
            action.triggered.connect(lambda _, p=full_path: self.open_file.emit(p))
            self.tool_bar_menu.addAction(action)
        self.tool_bar_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self.tool_bar_menu)
        clear_action.triggered.connect(self.clear_recent_files)

    def clear_recent_files(self):
        """Clear the recent files list."""
        self.recent_files = []
        self.save_recent_files()
        self.update_tool_bar_menu()
