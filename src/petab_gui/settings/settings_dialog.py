"""SettingsDialog - Pure UI layer for application settings.

This module contains the UI widgets for editing application settings,
including the main settings dialog and supporting widgets for table
column configuration.
"""

from PySide6.QtCore import Qt
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

from ..C import (
    ALLOWED_STRATEGIES,
    COPY_FROM,
    DEFAULT_VALUE,
    MODE,
    NO_DEFAULT,
    SOURCE_COLUMN,
    STRATEGIES_DEFAULT_ALL,
    STRATEGY_TOOLTIP,
    USE_DEFAULT,
)


class ColumnConfigWidget(QWidget):
    """Widget for editing a single column's configuration.

    Provides UI controls for configuring column default values, strategies,
    and source columns.

    Attributes
    ----------
    column_label : QLabel
        Label displaying the column name.
    strategy_choice : QComboBox
        Dropdown for selecting the default value strategy.
    default_value : QLineEdit
        Input field for the default value.
    source_column_dropdown : QComboBox
        Dropdown for selecting the source column (for copy strategies).
    """

    def __init__(
        self, column_name, config, table_columns, strategies=None, parent=None
    ):
        """
        Initialize the column configuration widget.

        Parameters
        ----------
        column_name : str
            Name of the column.
        config : dict
            Dictionary containing settings for the column.
        table_columns : list[str]
            List of columns in the same table (used for dropdown).
        strategies : list[str], optional
            List of allowed strategies for this column.
        parent : QWidget, optional
            Parent widget.
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

        for widget in [
            self.strategy_choice,
            self.default_value,
            self.source_column_dropdown,
        ]:
            widget.setFixedWidth(150)
            widget.setMinimumHeight(24)

        # Connect strategy selection to update UI
        self.strategy_choice.currentTextChanged.connect(self.update_ui)

        # Apply initial visibility state
        self.update_ui(self.strategy_choice.currentText())

    def add_aligned_row(self, label_text, widget):
        """Add a row of constant size to the FormLayout.

        Parameters
        ----------
        label_text : str
            The label text for the row.
        widget : QWidget
            The widget to add to the row.

        Returns
        -------
        QWidget
            The container widget for the row.
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(widget)
        self.layout.addRow(QLabel(label_text), container)
        return container

    def update_ui(self, strategy):
        """Show/hide relevant fields based on selected strategy.

        Parameters
        ----------
        strategy : str
            The currently selected strategy.
        """
        self.layout.setRowVisible(
            self.source_column_row, strategy == COPY_FROM
        )
        self.layout.setRowVisible(
            self.default_value_row, strategy == USE_DEFAULT
        )

    def get_current_config(self):
        """Return the current configuration from the UI.

        Returns
        -------
        dict
            Dictionary containing the current configuration.
        """
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
    """Widget for editing an entire table's default settings.

    Displays configuration widgets for all columns in a table, allowing
    users to set default values and strategies for each column.

    Attributes
    ----------
    table_name : str
        The name of the table being configured.
    column_widgets : dict[str, ColumnConfigWidget]
        Dictionary mapping column names to their configuration widgets.
    """

    def __init__(self, table_name, table_columns, settings, parent=None):
        """
        Initialize the table defaults widget.

        Parameters
        ----------
        table_name : str
            The name of the table.
        table_columns : list[str]
            List of column names in this table.
        settings : dict
            Dictionary of settings for this table.
        parent : QWidget, optional
            Parent widget.
        """
        super().__init__(parent)
        self.table_name = table_name
        self.setWindowTitle(f"{table_name.capitalize()} Table")

        # Import here to avoid circular imports at module load time
        from ..settings_manager import settings_manager

        self.settings_manager = settings_manager

        # Use QGroupBox for better title visibility
        group_box = QGroupBox(f"{table_name.capitalize()} Table")
        group_layout = QVBoxLayout(group_box)

        self.column_widgets = {}
        allowed_strats = ALLOWED_STRATEGIES.get(table_name, {})
        # Iterate over columns and create widgets
        for column_name in table_columns:
            column_settings = settings.get(
                column_name, self.default_col_config()
            )
            strategies = allowed_strats.get(column_name, None)
            column_widget = ColumnConfigWidget(
                column_name, column_settings, table_columns, strategies
            )
            column_widget.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Minimum
            )
            group_layout.addWidget(column_widget)
            self.column_widgets[column_name] = column_widget

        group_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Apply layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(group_box)
        self.setLayout(main_layout)

    def save_current_settings(self):
        """Retrieve settings from all column widgets and save them.

        Iterates through all column configuration widgets and saves their
        current state to the settings manager.
        """
        table_settings = {}

        for column_name, column_widget in self.column_widgets.items():
            table_settings[column_name] = column_widget.get_current_config()
        self.settings_manager.set_table_defaults(
            self.table_name, table_settings
        )

    def default_col_config(self):
        """Return default config for new columns.

        Returns
        -------
        dict
            Default configuration for a column.
        """
        return self.settings_manager.get_table_defaults(self.table_name)


class SettingsDialog(QDialog):
    """Dialog for editing application settings.

    Main settings dialog with navigation sidebar and multiple pages for
    different setting categories (General, Table Defaults).

    Attributes
    ----------
    table_columns : dict[str, list[str]]
        Dictionary mapping table names to their column lists.
    settings : dict
        Current settings loaded from the settings manager.
    nav_list : QListWidget
        Navigation list for switching between settings pages.
    content_stack : QStackedWidget
        Stacked widget containing the settings pages.
    forms : dict
        Dictionary containing form input widgets.
    table_widgets : dict[str, TableDefaultsWidget]
        Dictionary mapping table names to their configuration widgets.
    """

    def __init__(self, table_columns, parent=None):
        """Initialize the settings dialog.

        Parameters
        ----------
        table_columns : dict[str, list[str]]
            Dictionary mapping table names to their column lists.
        parent : QWidget, optional
            Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.table_columns = table_columns

        # Import here to avoid circular imports at module load time
        from ..settings_manager import settings_manager

        self.settings_manager = settings_manager
        self.settings = {
            table_type: self.settings_manager.get_value(
                f"table_defaults/{table_type}", {}
            )
            for table_type in table_columns
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
        """Switch to the selected settings page.

        Parameters
        ----------
        index : int
            The index of the page to switch to.
        """
        self.content_stack.setCurrentIndex(index)

    def init_general_page(self):
        """Create the general settings page.

        Builds the UI for general application settings like user profile
        information (name, email, organization).
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # Header
        header = QLabel("<b>Profile</b>")
        desc = QLabel(
            "These information can be automatically used when saving "
            "a COMBINE archive."
        )
        desc.setWordWrap(True)

        layout.addWidget(header)
        layout.addWidget(desc)

        # Form
        form = QFormLayout()
        self.forms = {
            "general": {
                "family_name": None,
                "given_name": None,
                "email": None,
                "orga": None,
            }
        }
        for key in self.forms["general"]:
            self.forms["general"][key] = QLineEdit(
                self.settings_manager.get_value(f"general/{key}", "")
            )
            self.forms["general"][key].setMinimumWidth(250)

        form.addRow("Family Name:", self.forms["general"]["family_name"])
        form.addRow("Given Name:", self.forms["general"]["given_name"])
        form.addRow("Email:", self.forms["general"]["email"])
        form.addRow("Organization:", self.forms["general"]["orga"])

        layout.addLayout(form)
        page.setLayout(layout)
        self._add_buttons(page)
        self.content_stack.addWidget(page)

    def init_table_defaults_page(self):
        """Create the table defaults settings page.

        Builds the UI for configuring table-specific default values and
        strategies in a scrollable grid layout.
        """
        page = QWidget()
        layout = QVBoxLayout(page)  # Vertical layout for stacking tables

        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow resizing
        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)

        self.table_widgets = {}
        # Add tables in a 2x2 grid
        for i_table, (table_name, column_list) in enumerate(
            self.table_columns.items()
        ):
            table_widget = TableDefaultsWidget(
                table_name, column_list, self.settings.get(table_name, {})
            )
            grid_layout.addWidget(table_widget, i_table // 2, i_table % 2)
            self.table_widgets[table_name] = table_widget

        scroll_content.setLayout(grid_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        self._add_buttons(page)
        self.content_stack.addWidget(page)

    def _add_buttons(self, page: QWidget):
        """Add Apply and Cancel buttons to a settings page.

        Parameters
        ----------
        page : QWidget
            The page widget to add buttons to.
        """
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.cancel_button = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        page.layout().addLayout(button_layout)

        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_settings)
        self.apply_button.setDefault(True)
        self.apply_button.setAutoDefault(True)
        self.cancel_button.setAutoDefault(False)

    def apply_settings(self):
        """Retrieve UI settings and save them in SettingsManager.

        Called when the user clicks the Apply button. Saves all changed
        settings and emits a log message.
        """
        # Save general settings
        for key in self.forms["general"]:
            self.settings_manager.set_value(
                f"general/{key}", self.forms["general"][key].text()
            )

        # Save table defaults
        for _table_name, table_widget in self.table_widgets.items():
            table_widget.save_current_settings()

        self.settings_manager.new_log_message.emit(
            "New settings applied.", "green"
        )
        self.accept()
