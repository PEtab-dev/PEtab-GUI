from PySide6.QtWidgets import QMessageBox, QMenu
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction

from ..settings_manager import settings_manager


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

    def load_recent_files(self):
        """Load recent files from settings."""
        return settings_manager.get_value("recent_files", [])

    def save_recent_files(self):
        """Save recent files to settings."""
        settings_manager.set_value("recent_files", self.recent_files)

    def update_tool_bar_menu(self):
        """Update the recent files menu."""
        self.tool_bar_menu.clear()
        for file_path in self.recent_files:
            action = QAction(file_path, self.tool_bar_menu)
            action.triggered.connect(lambda _, p=file_path: self.open_file.emit(p))  # Fix lambda issue
            self.tool_bar_menu.addAction(action)
        self.tool_bar_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self.tool_bar_menu)
        clear_action.triggered.connect(self.clear_recent_files)
        self.tool_bar_menu.addAction(clear_action)

    def clear_recent_files(self):
        """Clear the recent files list."""
        self.recent_files = []
        self.save_recent_files()
        self.update_tool_bar_menu()
