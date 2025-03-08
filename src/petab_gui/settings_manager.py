"""Create a SettingsManager class to handle application settings with
persistent storage.

Creates a single instance that will be imported and used."""
from PySide6.QtCore import QSettings, QObject, Signal


class SettingsManager(QObject):
    """Handles application settings with persistent storage."""

    settings_changed = Signal(str)  # Signal emitted when a setting is updated

    def __init__(self):
        """Initialize settings storage."""
        super().__init__()
        self.settings = QSettings("petab", "petab_gui")

    def get_value(self, key, default=None, value_type=None):
        """Retrieve a setting with an optional type conversion."""
        if value_type:
            return self.settings.value(key, default, type=value_type)
        return self.settings.value(key, default)

    def set_value(self, key, value):
        """Store a setting and emit a signal when changed."""
        self.settings.setValue(key, value)
        self.settings_changed.emit(key)  # Notify listeners

    def load_ui_settings(self, main_window):
        """Load UI-related settings such as main window and dock states."""
        # Restore main window geometry and state
        main_window.restoreGeometry(self.get_value("main_window/geometry", main_window.saveGeometry()))
        main_window.restoreState(self.get_value("main_window/state", main_window.saveState()))

        # Restore dock widget visibility
        for dock, _ in main_window.dock_visibility.items():
            dock.setVisible(self.get_value(
                f"docks/{dock.objectName()}", True, value_type=bool
            ))

        main_window.data_tab.restoreGeometry(self.get_value(
            "data_tab/geometry", main_window.data_tab.saveGeometry()
        ))
        main_window.data_tab.restoreState(self.get_value(
            "data_tab/state", main_window.data_tab.saveState()
        ))

    def save_ui_settings(self, main_window):
        """Save UI-related settings such as main window and dock states."""
        # Save main window geometry and state
        self.set_value("main_window/geometry", main_window.saveGeometry())
        self.set_value("main_window/state", main_window.saveState())

        # Save dock widget visibility
        for dock, _ in main_window.dock_visibility.items():
            self.set_value(f"docks/{dock.objectName()}", dock.isVisible())

        # Save data tab settings
        self.set_value(
            "data_tab/geometry", main_window.data_tab.saveGeometry()
        )
        self.set_value(
            "data_tab/state", main_window.data_tab.saveState()
        )


# Create a single instance of the SettingsManager to be imported and used
settings_manager = SettingsManager()