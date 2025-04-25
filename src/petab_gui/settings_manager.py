"""Create a SettingsManager class to handle application settings with
persistent storage.

Creates a single instance that will be imported and used.
"""
from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .C import (
    ALLOWED_STRATEGIES,
    COPY_FROM,
    DEFAULT_CONFIGS,
    DEFAULT_VALUE,
    MODE,
    NO_DEFAULT,
    SOURCE_COLUMN,
    STRATEGIES_DEFAULT_ALL,
    STRATEGY_TOOLTIP,
    USE_DEFAULT,
)


class SettingsManager(QObject):
    """Handles application settings with persistent storage."""

    settings_changed = Signal(str)  # Signal emitted when a setting is updated
    new_log_message = Signal(str, str)  # message, color

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

    def get_table_defaults(self, table_name):
        """Retrieve default configuration for a specific table."""
        return self.settings.value(
            f"table_defaults/{table_name}",
            DEFAULT_CONFIGS.get(table_name, {})
        )

    def set_table_defaults(self, table_name, config):
        """Update default configuration for a specific table."""
        self.settings.setValue(f"table_defaults/{table_name}", config)
        self.settings_changed.emit(f"table_defaults/{table_name}")


# Create a single instance of the SettingsManager to be imported and used
settings_manager = SettingsManager()


class ColumnConfigWidget(QWidget):
    """Widget for editing a single column's configuration."""

    def __init__(self, column_name, config, table_columns,
                 strategies=None, parent=None):
        """
        :param column_name: Name of the column
        :param config: Dictionary containing settings for the column
        :param table_columns: List of columns in the same table (used for dropdown)
        """
        super().__init__(parent)
        self.setWindowTitle(column_name)
        self.config = config
        self.table_columns = table_columns

        # Main vertical layout
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Column Name (Bold Title)
        self.column_label = QLabel(f"<b>{column_name}</b>")
        self.column_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.column_label)

        # Form layout for settings
        self.layout = QFormLayout()
        self.layout.setLabelAlignment(Qt.AlignRight)
        main_layout.addLayout(self.layout)

        # Strategy Dropdown
        self.strategy_choice = QComboBox()
        self.strategies = strategies if strategies else STRATEGIES_DEFAULT_ALL
        self.strategy_choice.addItems(self.strategies)
        self.strategy_choice.setCurrentText(config.get("strategy", NO_DEFAULT))
        self.strategy_choice.setToolTip(
            STRATEGY_TOOLTIP.get(self.strategy_choice.currentText(), "")
        )
        self.strategy_choice.currentTextChanged.connect(
            lambda text: self.strategy_choice.setToolTip(
                STRATEGY_TOOLTIP.get(text, "")
            )
        )
        self.strategy_row = self.add_aligned_row(
            "Strategy:", self.strategy_choice
        )
        # Default Value Input
        self.default_value = QLineEdit(str(config.get(DEFAULT_VALUE, "")))
        self.default_value_row = self.add_aligned_row(
            "Default Value:", self.default_value
        )
        # Source Column Dropdown (Only for "copy_column")
        self.source_column_dropdown = QComboBox()
        self.source_column_dropdown.addItems([""] + table_columns)
        self.source_column_dropdown.setCurrentText(
            config.get(SOURCE_COLUMN, "")
        )
        self.source_column_row = self.add_aligned_row(
            "Source Column:", self.source_column_dropdown
        )

        for widget in [self.strategy_choice, self.default_value,
                       self.source_column_dropdown]:
            widget.setFixedWidth(150)
            widget.setMinimumHeight(24)

        # Connect strategy selection to update UI
        self.strategy_choice.currentTextChanged.connect(self.update_ui)

        # Apply initial visibility state
        self.update_ui(self.strategy_choice.currentText())

    def add_aligned_row(self, label_text, widget):
        """Add a row of constant size to the FormLayout."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(widget)
        self.layout.addRow(QLabel(label_text), container)
        return container

    def update_ui(self, strategy):
        """Show/hide relevant fields based on selected strategy."""
        self.layout.setRowVisible(
            self.source_column_row, strategy == COPY_FROM
        )
        self.layout.setRowVisible(
            self.default_value_row, strategy == USE_DEFAULT
        )

    def get_current_config(self):
        """Return the current configuration from the UI."""
        config = {
            "strategy": self.strategy_choice.currentText(),
            DEFAULT_VALUE: self.default_value.text(),
        }
        if config["strategy"] == COPY_FROM:
            config[SOURCE_COLUMN] = self.source_column_dropdown.currentText()
        if config["strategy"] == MODE:
            config[SOURCE_COLUMN] = SOURCE_COLUMN  # Placeholder

        return config


class TableDefaultsWidget(QWidget):
    """Widget for editing an entire table's default settings."""

    def __init__(self, table_name, table_columns, settings, parent=None):
        """
        :param table_name: The name of the table
        :param table_columns: List of column names in this table
        :param settings: Dictionary of settings for this table
        """
        super().__init__(parent)
        self.table_name = table_name
        self.setWindowTitle(f"{table_name.capitalize()} Table")

        # Use QGroupBox for better title visibility
        group_box = QGroupBox(f"{table_name.capitalize()} Table")
        group_layout = QVBoxLayout(group_box)

        self.column_widgets = {}
        allowed_strats = ALLOWED_STRATEGIES.get(table_name, {})
        # Iterate over columns and create widgets
        for column_name in table_columns:
            column_settings = settings.get(column_name, self.default_col_config())
            strategies = allowed_strats.get(column_name, None)
            column_widget = ColumnConfigWidget(
                column_name, column_settings, table_columns, strategies
            )
            column_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            group_layout.addWidget(column_widget)
            self.column_widgets[column_name] = column_widget

        group_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Apply layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(group_box)
        self.setLayout(main_layout)

    def save_current_settings(self):
        """Retrieve settings from all column widgets."""
        table_settings = {}

        for column_name, column_widget in self.column_widgets.items():
            table_settings[column_name] = column_widget.get_current_config()
        settings_manager.set_table_defaults(self.table_name, table_settings)

    def default_col_config(self):
        """Return default config for new columns."""
        return {
            "strategy": NO_DEFAULT
        }


class SettingsDialog(QDialog):
    """Dialog for editing application settings."""

    def __init__(self, table_columns, parent=None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.table_columns = table_columns
        self.settings = {
            table_type: settings_manager.get_value(
                f"table_defaults/{table_type}", {}
            ) for table_type in table_columns.keys()
        }

        self.main_layout = QHBoxLayout(self)

        self.nav_list = QListWidget()
        self.nav_list.addItems(["General", "Table Defaults"])
        self.nav_list.currentRowChanged.connect(self.switch_page)
        self.main_layout.addWidget(self.nav_list, 1)

        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack, 3)

        # add pages to the stack
        self.init_general_page()
        self.init_table_defaults_page()

        self.nav_list.setCurrentRow(0)

    def switch_page(self, index):
        """Switch to the selected settings page."""
        self.content_stack.setCurrentIndex(index)

    def init_general_page(self):
        """Create the general settings page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("General settings (to be implemented)"))

        self.content_stack.addWidget(page)

    def init_table_defaults_page(self):
        """Create the table defaults settings page."""
        page = QWidget()
        layout = QVBoxLayout(page)  # Vertical layout for stacking tables

        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow resizing
        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)

        self.table_widgets = {}
        # Add tables in a 2x2 grid
        for i_table, (table_name, column_list) in enumerate(self.table_columns.items()):
            table_widget = TableDefaultsWidget(table_name, column_list, self.settings.get(table_name, {}))
            grid_layout.addWidget(table_widget, i_table // 2, i_table % 2)
            self.table_widgets[table_name] = table_widget

        scroll_content.setLayout(grid_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.cancel_button = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        layout.addLayout(button_layout)

        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_settings)
        self.content_stack.addWidget(page)

    def apply_settings(self):
        """Retrieve UI settings and save them in SettingsManager."""
        for table_name, table_widget in self.table_widgets.items():
            table_widget.save_current_settings()
        settings_manager.new_log_message.emit("New settings applied.", "green")
        self.accept()

