import logging
import math
import os
import re
from typing import Any

import antimony
import numpy as np
import pandas as pd
import petab.v1 as petab
import qtawesome as qta
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.figure import Figure
from PySide6.QtCore import QModelIndex, QObject, Qt, Signal
from PySide6.QtGui import QAction, QColor, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (
    QCheckBox,
    QCompleter,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .C import COLUMN, INDEX, ROW


def _checkAntimonyReturnCode(code):
    """Helper for checking the antimony response code.

    Raises Exception if error in antimony.

    :param code: antimony response
    :type code: int
    """
    if code < 0:
        raise Exception(f"Antimony: {antimony.getLastError()}")


def sbmlToAntimony(sbml):
    """Convert SBML to antimony string.

    :param sbml: SBML string or file
    :type sbml: str | file
    :return: Antimony
    :rtype: str
    """
    antimony.clearPreviousLoads()
    antimony.freeAll()
    isfile = False
    try:
        isfile = os.path.isfile(sbml)
    except Exception as e:
        logging.warning(f"Error checking if {sbml} is a file: {str(e)}")
        isfile = False
    if isfile:
        code = antimony.loadSBMLFile(sbml)
    else:
        code = antimony.loadSBMLString(str(sbml))
    _checkAntimonyReturnCode(code)
    return antimony.getAntimonyString(None)


def antimonyToSBML(ant):
    """Convert Antimony to SBML string.

    :param ant: Antimony string or file
    :type ant: str | file
    :return: SBML
    :rtype: str
    """
    antimony.clearPreviousLoads()
    antimony.freeAll()
    try:
        isfile = os.path.isfile(ant)
    except ValueError:
        isfile = False
    if isfile:
        code = antimony.loadAntimonyFile(ant)
    else:
        code = antimony.loadAntimonyString(ant)
    _checkAntimonyReturnCode(code)
    mid = antimony.getMainModuleName()
    return antimony.getSBMLString(mid)


class ConditionInputDialog(QDialog):
    """Dialog for adding or editing experimental conditions.

    Provides input fields for simulation condition ID and optional
    preequilibration condition ID.
    """

    def __init__(self, condition_id=None, parent=None):
        """Initialize the condition input dialog.

        Args:
        condition_id:
            Optional initial value for the simulation condition ID
        parent:
            The parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Add Condition")

        self.layout = QVBoxLayout(self)
        self.notification_label = QLabel("", self)
        self.notification_label.setStyleSheet("color: red;")
        self.notification_label.setVisible(False)
        self.layout.addWidget(self.notification_label)

        # Simulation Condition
        sim_layout = QHBoxLayout()
        sim_label = QLabel("Simulation Condition:", self)
        self.sim_input = QLineEdit(self)
        if condition_id:
            self.sim_input.setText(condition_id)
        sim_layout.addWidget(sim_label)
        sim_layout.addWidget(self.sim_input)
        self.layout.addLayout(sim_layout)

        # Preequilibration Condition
        preeq_layout = QHBoxLayout()
        preeq_label = QLabel("Preequilibration Condition:", self)
        self.preeq_input = QLineEdit(self)
        self.preeq_input.setToolTip(
            "This field is only needed when your experiment started in steady "
            "state. In this case add here the experimental condition id for "
            "the steady state."
        )
        preeq_layout.addWidget(preeq_label)
        preeq_layout.addWidget(self.preeq_input)
        self.layout.addLayout(preeq_layout)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.buttons_layout.addWidget(self.ok_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.buttons_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def accept(self):
        """Override the accept method to validate inputs before accepting.

        Checks if the simulation condition ID is provided.
        If not, shows an error message and prevents the dialog from closing.
        """
        if not self.sim_input.text().strip():
            self.sim_input.setStyleSheet("background-color: red;")
            self.notification_label.setText(
                "Simulation Condition is required."
            )
            self.notification_label.setVisible(True)
            return
        self.notification_label.setVisible(False)
        self.sim_input.setStyleSheet("")
        super().accept()

    def get_inputs(self):
        """Get the user inputs as a dictionary.

        Returns:
        A dictionary containing:
            - 'simulationConditionId': The simulation condition ID
            - 'preequilibrationConditionId': The preequilibration condition ID
              (only included if provided)
        """
        inputs = {}
        inputs["simulationConditionId"] = self.sim_input.text()
        preeq = self.preeq_input.text()
        if preeq:
            inputs["preequilibrationConditionId"] = preeq
        return inputs


def validate_value(value, expected_type):
    """Validate and convert a value to the expected type.

    Args:
        value: The value to validate and convert
        expected_type: The numpy type to convert the value to

    Returns:
        tuple: A tuple containing:
            - The converted value, or None if conversion failed
            - An error message if conversion failed, or None if successful
    """
    try:
        if expected_type == np.object_:
            value = str(value)
        elif expected_type == np.float64:
            value = float(value)
    except ValueError as e:
        return None, str(e)
    return value, None


class PlotWidget(FigureCanvas):
    """A widget for displaying matplotlib plots in Qt applications.

    Inherits from FigureCanvas to provide a Qt widget that can display
    matplotlib figures.
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """Initialize the plot widget.

        Args:
            parent: The parent widget
            width: The width of the figure in inches
            height: The height of the figure in inches
            dpi: The resolution of the figure in dots per inch
        """
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


def create_empty_dataframe(column_dict: dict, table_type: str):
    """Create an empty pandas DataFrame with the specified columns and types.

    Args:
    column_dict:
        A dictionary mapping column names to their properties, where each
        property dict contains 'optional' and 'type' keys
    table_type:
        The type of table to create ('observable', 'parameter',
        or 'condition') which determines the index column

    Returns:
        pd.DataFrame: An empty DataFrame with the specified columns and index
    """
    columns = [
        col for col, props in column_dict.items() if not props["optional"]
    ]
    dtypes = {
        col: props["type"]
        for col, props in column_dict.items()
        if not props["optional"]
    }
    df = pd.DataFrame(columns=columns).astype(dtypes)
    # set potential index columns
    if table_type == "observable":
        df.set_index(petab.C.OBSERVABLE_ID, inplace=True)
    elif table_type == "parameter":
        df.set_index(petab.C.PARAMETER_ID, inplace=True)
    elif table_type == "condition":
        df.set_index(petab.C.CONDITION_ID, inplace=True)
    return df


class CaptureLogHandler(logging.Handler):
    """A logging handler to capture log messages with levels."""

    def __init__(self):
        """Initialize the log handler.

        Creates an empty list to store log records.
        """
        super().__init__()
        self.records = []  # Store full log records

    def emit(self, record):
        """Process a log record by storing it in the records list.

        Args:
            record: The LogRecord to process
        """
        self.records.append(record)  # Save the entire LogRecord

    def get_formatted_messages(self):
        """Return formatted messages with levels."""
        return [
            f"{record.levelname}: {self.format(record)}"
            for record in self.records
        ]


def get_selected(
    table_view: QTableView, mode: str = ROW
) -> list[Any] | list[QModelIndex] | set[int] | None:
    """
    Determines which items are selected in a QTableView.

    Args:
        table_view (QTableView): The table view to check.
        mode (str): The selection mode to use. Can be one of:
            - ROW: Return selected row indices
            - COLUMN: Return selected column indices
            - INDEX: Return selected model indices

    Returns:
        list[int] or set[int] or list[QModelIndex]:
            - If mode is ROW: A set of selected row indices
            - If mode is COLUMN: A set of selected column indices
            - If mode is INDEX: A list of selected QModelIndex objects
    """
    if not table_view or not isinstance(table_view, QTableView):
        return []
    if mode not in [ROW, COLUMN, INDEX]:
        return []

    selection_model = table_view.selectionModel()
    if not selection_model:
        return []
    selected_indexes = selection_model.selectedIndexes()
    if mode == INDEX:
        return selected_indexes
    if mode == COLUMN:
        return {index.column() for index in selected_indexes}
    if mode == ROW:
        return {index.row() for index in selected_indexes}
    return None


def get_selected_rectangles(table_view: QTableView) -> np.array:
    """Returns the selected cells in a rectangular view.

    The size of the rectangle is determined by Max_row - Min_row and
    Max_column - Min_column. The returned array is a boolean array with
    True values for selected cells.
    """
    selected = get_selected(table_view, mode=INDEX)
    if not selected:
        return None

    model = table_view.model()
    if hasattr(model, "mapToSource"):
        # map all indices to source
        selected = [model.mapToSource(index) for index in selected]

    rows = [index.row() for index in selected]
    cols = [index.column() for index in selected]
    min_row, max_row = min(rows), max(rows)
    min_col, max_col = min(cols), max(cols)
    rect_start = (min_row, min_col)
    selected_rect = np.zeros(
        (max_row - min_row + 1, max_col - min_col + 1), dtype=bool
    )
    for index in selected:
        selected_rect[index.row() - min_row, index.column() - min_col] = True

    return selected_rect, rect_start


def process_file(filepath, logger):
    """
    Utility function to process a file based on its type and content.

    Args:
        filepath (str): Path to the file to process.
        logger: A logger object with a log_message method for reporting errors.

    Returns:
    A tuple containing:
        - The detected file type (or None if not recognized)
        - The detected separator for tabular files (or None if not applicable)
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    # Case 1: YAML files
    if ext in {".yaml", ".yml"}:
        return "yaml", None

    # Case 2: XML/SBML files
    if ext in {".xml", ".sbml"}:
        return "sbml", None

    # Case 3: CSV/TSV/TXT files
    if ext in {".csv", ".tsv", ".txt"}:
        separators = [",", "\t", ";"]
        separator = None
        header = None

        for sep in separators:
            # read the first line of the file
            try:
                with open(filepath, encoding="utf-8") as file:
                    header = file.readline().strip().split(sep)
                if len(header) > 1:
                    separator = sep
                    break
            except Exception as e:
                logging.debug(
                    f"Failed to read file with separator '{sep}': {str(e)}"
                )
                continue

        if header is None:
            logger.log_message(
                f"Failed to read file: {filepath}. Perhaps unsupported "
                f"delimiter. Supported delimiters: {', '.join(separators)}",
                color="red",
            )
            return None, None

        # Case 3.2: Identify the table type based on header content
        if {petab.C.OBSERVABLE_ID, petab.C.MEASUREMENT, petab.C.TIME}.issubset(
            header
        ):
            return "measurement", separator
        if {petab.C.OBSERVABLE_ID, petab.C.SIMULATION, petab.C.TIME}.issubset(
            header
        ):
            return "simulation", separator
        if {petab.C.OBSERVABLE_ID, petab.C.OBSERVABLE_FORMULA}.issubset(
            header
        ):
            return "observable", separator
        if petab.C.PARAMETER_ID in header:
            return "parameter", separator
        if (
            petab.C.CONDITION_ID in header
            or f"\ufeff{petab.C.CONDITION_ID}" in header
        ):
            return "condition", separator
        if petab.C.PLOT_ID in header:
            return "visualization", separator
        logger.log_message(
            f"Unrecognized table type for file: {filepath}. Uploading as "
            f"data matrix.",
            color="orange",
        )
        return "data_matrix", separator

    # Case 4: Combine Archive
    if ext in {".omex"}:
        return "omex", None

    logger.log_message(
        f"Unrecognized file type for file: {filepath}.", color="red"
    )
    return None, None


def is_invalid(value):
    """Check if a value is invalid."""
    if value is None:  # None values are invalid
        return True
    if isinstance(value, str):  # Strings can always be displayed
        return False
    try:
        return not math.isfinite(value)
    except TypeError:
        return True
