"""SettingsModel - Pure data and persistence layer for application settings.

This module contains the SettingsModel class, which handles persistent storage
of application settings using QSettings, without any UI dependencies.
"""

from PySide6.QtCore import QObject, QSettings, Signal

from ..C import DEFAULT_CONFIGS


class SettingsModel(QObject):
    """Handles application settings with persistent storage.

    This is a pure data/persistence layer that manages settings storage
    using QSettings. It has no UI dependencies and emits signals when
    settings change.

    Attributes
    ----------
    settings : QSettings
        The Qt settings storage backend.
    settings_changed : Signal
        Emitted when a setting is updated (passes the key as string).
    new_log_message : Signal
        Emitted when a log message should be displayed (passes message and color).
    """

    settings_changed = Signal(str)  # Signal emitted when a setting is updated
    new_log_message = Signal(str, str)  # message, color

    def __init__(self):
        """Initialize settings storage."""
        super().__init__()
        self.settings = QSettings("petab", "petab_gui")

    def get_value(self, key, default=None, value_type=None):
        """Retrieve a setting with an optional type conversion.

        Parameters
        ----------
        key : str
            The settings key to retrieve.
        default : any, optional
            Default value if the key doesn't exist.
        value_type : type, optional
            Type to convert the value to (e.g., bool, int, str).

        Returns
        -------
        any
            The setting value, converted to value_type if specified.
        """
        if value_type:
            return self.settings.value(key, default, type=value_type)
        return self.settings.value(key, default)

    def set_value(self, key, value):
        """Store a setting and emit a signal when changed.

        Parameters
        ----------
        key : str
            The settings key to store.
        value : any
            The value to store.
        """
        self.settings.setValue(key, value)
        self.settings_changed.emit(key)  # Notify listeners

    def load_ui_settings(self, main_window):
        """Load UI-related settings such as main window and dock states.

        Parameters
        ----------
        main_window : MainWindow
            The main window whose state should be restored.
        """
        # Restore main window geometry and state
        main_window.restoreGeometry(
            self.get_value("main_window/geometry", main_window.saveGeometry())
        )
        main_window.restoreState(
            self.get_value("main_window/state", main_window.saveState())
        )

        # Restore dock widget visibility
        for dock, _ in main_window.dock_visibility.items():
            dock.setVisible(
                self.get_value(
                    f"docks/{dock.objectName()}", True, value_type=bool
                )
            )

        main_window.data_tab.restoreGeometry(
            self.get_value(
                "data_tab/geometry", main_window.data_tab.saveGeometry()
            )
        )
        main_window.data_tab.restoreState(
            self.get_value("data_tab/state", main_window.data_tab.saveState())
        )

    def save_ui_settings(self, main_window):
        """Save UI-related settings such as main window and dock states.

        Parameters
        ----------
        main_window : MainWindow
            The main window whose state should be saved.
        """
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
        self.set_value("data_tab/state", main_window.data_tab.saveState())

    def get_table_defaults(self, table_name):
        """Retrieve default configuration for a specific table.

        Parameters
        ----------
        table_name : str
            The name of the table.

        Returns
        -------
        dict
            Dictionary containing the table's default configuration.
        """
        return self.settings.value(
            f"table_defaults/{table_name}", DEFAULT_CONFIGS.get(table_name, {})
        )

    def set_table_defaults(self, table_name, config):
        """Update default configuration for a specific table.

        Parameters
        ----------
        table_name : str
            The name of the table.
        config : dict
            Dictionary containing the new configuration.
        """
        self.settings.setValue(f"table_defaults/{table_name}", config)
        self.settings_changed.emit(f"table_defaults/{table_name}")
