import logging
import os
import re
import tempfile
import zipfile
from functools import partial
from importlib.metadata import version
from io import BytesIO
from pathlib import Path

import petab.v1 as petab
import qtawesome as qta
import yaml
from petab.versions import get_major_version
from PySide6.QtCore import QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QAction,
    QDesktopServices,
    QKeySequence,
    QUndoStack,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QTableView,
    QToolButton,
    QWhatsThis,
    QWidget,
)

from ..models import PEtabModel, SbmlViewerModel
from ..settings_manager import SettingsDialog, settings_manager
from ..utils import (
    CaptureLogHandler,
    get_selected,
    process_file,
)
from ..views import TaskBar
from .logger_controller import LoggerController
from .sbml_controller import SbmlController
from .table_controllers import (
    ConditionController,
    MeasurementController,
    ObservableController,
    ParameterController,
    VisualizationController,
)
from .utils import (
    RecentFilesManager,
    _WhatsThisClickHelp,
    filtered_error,
    prompt_overwrite_or_append,
)


class MainController:
    """Main controller class.

    Handles the communication between controllers. Handles general tasks.
    Mother controller to all other controllers. One controller to rule them
    all.
    """

    def __init__(self, view, model: PEtabModel):
        """Initialize the main controller.

        Parameters
        ----------
        view: MainWindow
            The main window.
        model: PEtabModel
            The PEtab model.
        """
        self.undo_stack = QUndoStack()
        self.task_bar = None
        self.view = view
        self.model = model
        self.logger = LoggerController(view.logger_views)
        # CONTROLLERS
        self.measurement_controller = MeasurementController(
            self.view.measurement_dock,
            self.model.measurement,
            self.logger,
            self.undo_stack,
            self,
        )
        self.observable_controller = ObservableController(
            self.view.observable_dock,
            self.model.observable,
            self.logger,
            self.undo_stack,
            self,
        )
        self.parameter_controller = ParameterController(
            self.view.parameter_dock,
            self.model.parameter,
            self.logger,
            self.undo_stack,
            self,
        )
        self.condition_controller = ConditionController(
            self.view.condition_dock,
            self.model.condition,
            self.logger,
            self.undo_stack,
            self,
        )
        self.visualization_controller = VisualizationController(
            self.view.visualization_dock,
            self.model.visualization,
            self.logger,
            self.undo_stack,
            self,
        )
        self.simulation_controller = MeasurementController(
            self.view.simulation_dock,
            self.model.simulation,
            self.logger,
            self.undo_stack,
            self,
        )
        self.sbml_controller = SbmlController(
            self.view.sbml_viewer, self.model.sbml, self.logger, self
        )
        self.controllers = [
            self.measurement_controller,
            self.observable_controller,
            self.parameter_controller,
            self.condition_controller,
            self.sbml_controller,
            self.visualization_controller,
            self.simulation_controller,
        ]
        # Recent Files
        self.recent_files_manager = RecentFilesManager(max_files=10)
        # Checkbox states for Find + Replace
        self.petab_checkbox_states = {
            "measurement": False,
            "observable": False,
            "parameter": False,
            "condition": False,
            "visualization": False,
            "simulation": False,
        }
        self.sbml_checkbox_states = {"sbml": False, "antimony": False}
        self.unsaved_changes = False
        self.filter = QLineEdit()
        self.filter_active = {}  # Saves which tables the filter applies to
        self.actions = self.setup_actions()
        self.view.setup_toolbar(self.actions)

        self.setup_connections()
        self.setup_task_bar()
        self.setup_context_menu()
        self.plotter = None
        self.init_plotter()

    @property
    def window_title(self):
        """Return the window title based on the model."""
        if isinstance(self.model.sbml, SbmlViewerModel):
            return self.model.sbml.model_id
        return "PEtabGUI"

    def setup_context_menu(self):
        """Sets up context menus for the tables."""
        for controller in self.controllers:
            if controller == self.sbml_controller:
                continue
            controller.setup_context_menu(self.actions)

    def setup_task_bar(self):
        """Create shortcuts for the main window."""
        self.view.task_bar = TaskBar(self.view, self.actions)
        self.task_bar = self.view.task_bar

    # CONNECTIONS
    def setup_connections(self):
        """Setup connections.

        Sets all connections that communicate from one different
        Models/Views/Controllers to another. Also sets general connections.
        """
        # Rename Observable
        self.observable_controller.observable_2be_renamed.connect(
            partial(
                self.measurement_controller.rename_value,
                column_names="observableId",
            )
        )
        # Rename Condition
        self.condition_controller.condition_2be_renamed.connect(
            partial(
                self.measurement_controller.rename_value,
                column_names=[
                    "simulationConditionId",
                    "preequilibrationConditionId",
                ],
            )
        )
        # Add new condition or observable
        self.model.measurement.relevant_id_changed.connect(
            lambda x, y, z: self.observable_controller.maybe_add_observable(
                x, y
            )
            if z == "observable"
            else self.condition_controller.maybe_add_condition(x, y)
            if z == "condition"
            else None
        )
        # Maybe Move to a Plot Model
        self.view.measurement_dock.table_view.selectionModel().selectionChanged.connect(
            self._on_table_selection_changed
        )
        self.view.simulation_dock.table_view.selectionModel().selectionChanged.connect(
            self._on_simulation_selection_changed
        )
        # Unsaved Changes
        self.model.measurement.something_changed.connect(
            self.unsaved_changes_change
        )
        self.model.observable.something_changed.connect(
            self.unsaved_changes_change
        )
        self.model.parameter.something_changed.connect(
            self.unsaved_changes_change
        )
        self.model.condition.something_changed.connect(
            self.unsaved_changes_change
        )
        self.model.visualization.something_changed.connect(
            self.unsaved_changes_change
        )
        self.model.simulation.something_changed.connect(
            self.unsaved_changes_change
        )
        self.model.sbml.something_changed.connect(self.unsaved_changes_change)
        # Visibility
        self.sync_visibility_with_actions()
        # Recent Files
        self.recent_files_manager.open_file.connect(
            partial(self.open_file, mode="overwrite")
        )
        # Settings logging
        settings_manager.new_log_message.connect(self.logger.log_message)
        # Update Parameter SBML Model
        self.sbml_controller.overwritten_model.connect(
            self.parameter_controller.update_handler_sbml
        )
        # Plotting update. Regulated through a Timer
        self._plot_update_timer = QTimer()
        self._plot_update_timer.setSingleShot(True)
        self._plot_update_timer.setInterval(0)
        self._plot_update_timer.timeout.connect(self.init_plotter)
        for controller in [
            self.measurement_controller,
            self.condition_controller,
            self.visualization_controller,
            self.simulation_controller,
        ]:
            controller.overwritten_df.connect(self._schedule_plot_update)

    def setup_actions(self):
        """Setup actions for the main controller."""
        actions = {
            "close": QAction(qta.icon("mdi6.close"), "&Close", self.view)
        }
        # Close
        actions["close"].setShortcut(QKeySequence.Close)
        actions["close"].triggered.connect(self.view.close)
        # New File
        actions["new"] = QAction(
            qta.icon("mdi6.file-document"), "&New", self.view
        )
        actions["new"].setShortcut(QKeySequence.New)
        actions["new"].triggered.connect(self.new_file)
        # Open File
        actions["open"] = QAction(
            qta.icon("mdi6.folder-open"), "&Open...", self.view
        )
        actions["open"].setShortcut(QKeySequence.Open)
        actions["open"].triggered.connect(
            partial(self.open_file, mode="overwrite")
        )
        # Add File
        actions["add"] = QAction(qta.icon("mdi6.table-plus"), "Add", self.view)
        actions["add"].setShortcut("Ctrl+Shift+O")
        actions["add"].triggered.connect(
            partial(self.open_file, mode="append")
        )
        # Save
        actions["save"] = QAction(
            qta.icon("mdi6.content-save-all"), "&Save As...", self.view
        )
        actions["save"].setShortcut(QKeySequence.Save)
        actions["save"].triggered.connect(self.save_model)
        actions["save_single_table"] = QAction(
            qta.icon("mdi6.table-arrow-down"), "Save This Table", self.view
        )
        actions["save_single_table"].triggered.connect(self.save_single_table)
        # Find + Replace
        actions["find"] = QAction(qta.icon("mdi6.magnify"), "Find", self.view)
        actions["find"].setShortcut(QKeySequence.Find)
        actions["find"].triggered.connect(self.find)
        actions["find+replace"] = QAction(
            qta.icon("mdi6.find-replace"), "Find/Replace", self.view
        )
        actions["find+replace"].setShortcut(QKeySequence.Replace)
        actions["find+replace"].triggered.connect(self.replace)
        # Copy / Paste
        actions["copy"] = QAction(
            qta.icon("mdi6.content-copy"), "Copy", self.view
        )
        actions["copy"].setShortcut(QKeySequence.Copy)
        actions["copy"].triggered.connect(self.copy_to_clipboard)
        actions["paste"] = QAction(
            qta.icon("mdi6.content-paste"), "Paste", self.view
        )
        actions["paste"].setShortcut(QKeySequence.Paste)
        actions["paste"].triggered.connect(self.paste_from_clipboard)
        actions["cut"] = QAction(
            qta.icon("mdi6.content-cut"), "&Cut", self.view
        )
        actions["cut"].setShortcut(QKeySequence.Cut)
        actions["cut"].triggered.connect(self.cut)
        # add/delete row
        actions["add_row"] = QAction(
            qta.icon("mdi6.table-row-plus-after"), "Add Row", self.view
        )
        actions["add_row"].triggered.connect(self.add_row)
        actions["delete_row"] = QAction(
            qta.icon("mdi6.table-row-remove"), "Delete Row(s)", self.view
        )
        actions["delete_row"].triggered.connect(self.delete_rows)
        # add/delete column
        actions["add_column"] = QAction(
            qta.icon("mdi6.table-column-plus-after"),
            "Add Column...",
            self.view,
        )
        actions["add_column"].triggered.connect(self.add_column)
        actions["delete_column"] = QAction(
            qta.icon("mdi6.table-column-remove"), "Delete Column(s)", self.view
        )
        actions["delete_column"].triggered.connect(self.delete_column)
        # check petab model
        actions["check_petab"] = QAction(
            qta.icon("mdi6.checkbox-multiple-marked-circle-outline"),
            "Check PEtab",
            self.view,
        )
        actions["check_petab"].triggered.connect(self.check_model)
        actions["reset_model"] = QAction(
            qta.icon("mdi6.restore"), "Reset SBML Model", self.view
        )
        actions["reset_model"].triggered.connect(
            self.sbml_controller.reset_to_original_model
        )
        # Recent Files
        actions["recent_files"] = self.recent_files_manager.tool_bar_menu

        # simulate action
        actions["simulate"] = QAction(
            qta.icon("mdi6.play"), "Simulate", self.view
        )
        actions["simulate"].triggered.connect(self.simulate)

        # Filter widget
        filter_widget = QWidget()
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_widget.setLayout(filter_layout)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter...")
        filter_layout.addWidget(self.filter_input)
        for table_n, table_name in zip(
            ["m", "p", "o", "c", "v", "s"],
            [
                "measurement",
                "parameter",
                "observable",
                "condition",
                "visualization",
                "simulation",
            ],
            strict=False,
        ):
            tool_button = QToolButton()
            icon = qta.icon(
                f"mdi6.alpha-{table_n}",
                "mdi6.filter",
                options=[
                    {"scale_factor": 1.5, "offset": (-0.2, -0.2)},
                    {"off": "mdi6.filter-off", "offset": (0.3, 0.3)},
                ],
            )
            tool_button.setIcon(icon)
            tool_button.setCheckable(True)
            tool_button.setChecked(True)
            tool_button.setToolTip(f"Filter for {table_name} table")
            filter_layout.addWidget(tool_button)
            self.filter_active[table_name] = tool_button
            self.filter_active[table_name].toggled.connect(self.filter_table)
        actions["filter_widget"] = filter_widget
        self.filter_input.textChanged.connect(self.filter_table)

        # show/hide elements
        for element in [
            "measurement",
            "observable",
            "parameter",
            "condition",
            "visualization",
            "simulation",
        ]:
            actions[f"show_{element}"] = QAction(
                f"{element.capitalize()} Table", self.view
            )
            actions[f"show_{element}"].setCheckable(True)
            actions[f"show_{element}"].setChecked(True)
        actions["show_logger"] = QAction("Info", self.view)
        actions["show_logger"].setCheckable(True)
        actions["show_logger"].setChecked(True)
        actions["show_plot"] = QAction("Data Plot", self.view)
        actions["show_plot"].setCheckable(True)
        actions["show_plot"].setChecked(True)

        # What's This action
        actions["whats_this"] = QAction(
            qta.icon("mdi6.help-circle"), "Enter Help Mode", self.view
        )
        actions["whats_this"].setCheckable(True)
        actions["whats_this"].setShortcut("Shift+F1")
        self._whats_this_filter = _WhatsThisClickHelp(actions["whats_this"])
        actions["whats_this"].toggled.connect(self._toggle_whats_this_mode)

        # About action
        actions["about"] = QAction(
            qta.icon("mdi6.information"), "&About", self.view
        )
        actions["about"].triggered.connect(self.about)

        # connect actions
        actions["reset_view"] = QAction(
            qta.icon("mdi6.view-grid-plus"), "Reset View", self.view
        )
        actions["reset_view"].triggered.connect(self.view.default_view)
        # Clear Log
        actions["clear_log"] = QAction(
            qta.icon("mdi6.delete"), "Clear Log", self.view
        )
        actions["clear_log"].triggered.connect(self.logger.clear_log)
        # Settings
        actions["settings"] = QAction(
            qta.icon("mdi6.cog"), "Settings", self.view
        )
        actions["settings"].triggered.connect(self.open_settings)

        # Opening the PEtab documentation
        actions["open_documentation"] = QAction(
            qta.icon("mdi6.web"), "View PEtab Documentation", self.view
        )
        actions["open_documentation"].triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(
                    "https://petab.readthedocs.io/en/latest/v1/"
                    "documentation_data_format.html"
                )
            )
        )

        # Undo / Redo
        actions["undo"] = QAction(qta.icon("mdi6.undo"), "&Undo", self.view)
        actions["undo"].setShortcut(QKeySequence.Undo)
        actions["undo"].triggered.connect(self.undo_stack.undo)
        actions["undo"].setEnabled(self.undo_stack.canUndo())
        self.undo_stack.canUndoChanged.connect(actions["undo"].setEnabled)
        actions["redo"] = QAction(qta.icon("mdi6.redo"), "&Redo", self.view)
        actions["redo"].setShortcut(QKeySequence.Redo)
        actions["redo"].triggered.connect(self.undo_stack.redo)
        actions["redo"].setEnabled(self.undo_stack.canRedo())
        self.undo_stack.canRedoChanged.connect(actions["redo"].setEnabled)
        # Clear cells
        actions["clear_cells"] = QAction(
            qta.icon("mdi6.delete"), "&Clear Cells", self.view
        )
        actions["clear_cells"].setShortcuts(
            [QKeySequence.Delete, QKeySequence.Backspace]
        )
        actions["clear_cells"].triggered.connect(self.clear_cells)
        return actions

    def sync_visibility_with_actions(self):
        """Sync dock visibility and QAction states in both directions."""
        dock_map = {
            "measurement": self.view.measurement_dock,
            "observable": self.view.observable_dock,
            "parameter": self.view.parameter_dock,
            "condition": self.view.condition_dock,
            "logger": self.view.logger_dock,
            "plot": self.view.plot_dock,
            "visualization": self.view.visualization_dock,
            "simulation": self.view.simulation_dock,
        }

        for key, dock in dock_map.items():
            action = self.actions[f"show_{key}"]

            # Initial sync: block signal to avoid triggering unwanted
            # visibility changes
            was_blocked = action.blockSignals(True)
            action.setChecked(dock.isVisible())
            action.blockSignals(was_blocked)

            # Connect QAction ↔ DockWidget syncing
            action.toggled.connect(dock.setVisible)
            dock.visibilityChanged.connect(action.setChecked)

    def save_model(self):
        options = QFileDialog.Options()
        file_name, filtering = QFileDialog.getSaveFileName(
            self.view,
            "Save Project",
            "",
            "COMBINE Archive (*.omex);;Zip Files (*.zip);;Folder",
            options=options,
        )
        if not file_name:
            return False

        if filtering == "COMBINE Archive (*.omex)":
            self.model.save_as_omex(file_name)
        elif filtering == "Folder":
            if file_name.endswith("."):
                file_name = file_name[:-1]
            target = Path(file_name)
            target.mkdir(parents=True, exist_ok=True)
            self.model.save(str(target))
            file_name = str(target)
        else:
            if not file_name.endswith(".zip"):
                file_name += ".zip"

            # Create a temporary directory to save the model's files
            with tempfile.TemporaryDirectory() as temp_dir:
                self.model.save(temp_dir)

                # Create a bytes buffer to hold the zip file in memory
                buffer = BytesIO()
                with zipfile.ZipFile(buffer, "w") as zip_file:
                    # Add files to zip archive
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            with open(file_path, "rb") as f:
                                zip_file.writestr(file, f.read())
                with open(file_name, "wb") as f:
                    f.write(buffer.getvalue())

        QMessageBox.information(
            self.view,
            "Save Project",
            f"Project saved successfully to {file_name}",
        )
        return True

    def save_single_table(self):
        """Save the currently active table to a tsv-file."""
        active_controller = self.active_controller()
        if not active_controller:
            QMessageBox.warning(
                self.view,
                "Save Table",
                "No active table to save.",
            )
            return None
        file_name, _ = QFileDialog.getSaveFileName(
            self.view,
            "Save Table (as *.tsv)",
            f"{active_controller.model.table_type}.tsv",
            "TSV Files (*.tsv)",
        )
        if not file_name:
            return False
        active_controller.save_table(file_name)
        return True

    def handle_selection_changed(self):
        """Update the plot when selection in the measurement table changes."""
        self.update_plot()

    def handle_data_changed(self, top_left, bottom_right, roles):
        """Update the plot when the data in the measurement table changes."""
        if not roles or Qt.DisplayRole in roles:
            self.update_plot()

    def update_plot(self):
        """Update the plot with the selected measurement data.

        Extracts the selected data points from the measurement table and
        updates the plot visualization with this data.
        """
        selection_model = (
            self.view.measurement_dock.table_view.selectionModel()
        )
        indexes = selection_model.selectedIndexes()
        if not indexes:
            return

        selected_points = {}
        for index in indexes:
            if index.row() == self.model.measurement.get_df().shape[0]:
                continue
            row = index.row()
            observable_id = self.model.measurement._data_frame.iloc[row][
                "observableId"
            ]
            if observable_id not in selected_points:
                selected_points[observable_id] = []
            selected_points[observable_id].append(
                {
                    "x": self.model.measurement._data_frame.iloc[row]["time"],
                    "y": self.model.measurement._data_frame.iloc[row][
                        "measurement"
                    ],
                }
            )
        if selected_points == {}:
            return

        measurement_data = self.model.measurement._data_frame
        plot_data = {"all_data": [], "selected_points": selected_points}
        for observable_id in selected_points:
            observable_data = measurement_data[
                measurement_data["observableId"] == observable_id
            ]
            plot_data["all_data"].append(
                {
                    "observable_id": observable_id,
                    "x": observable_data["time"].tolist(),
                    "y": observable_data["measurement"].tolist(),
                }
            )

        self.view.plot_dock.update_visualization(plot_data)

    def open_file(self, file_path=None, mode=None):
        """Determines appropriate course of action for a given file.

        Course of action depends on file extension, separator and header
        structure. Opens the file in the appropriate controller.
        """
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self.view,
                "Open File",
                "",
                "All supported (*.yaml *.yml *.xml *.sbml *.tsv *.csv *.txt "
                "*.omex);;"
                "PEtab Problems (*.yaml *.yml);;SBML Files (*.xml *.sbml);;"
                "PEtab Tables or Data Matrix (*.tsv *.csv *.txt);;"
                "COMBINE Archive (*.omex);;"
                "All files (*)",
            )
        if not file_path:
            return
        # handle file appropriately
        actionable, sep = process_file(file_path, self.logger)
        if actionable in ["yaml", "sbml", "omex"] and mode == "append":
            self.logger.log_message(
                f"Append mode is not supported for *.{actionable} files.",
                color="red",
            )
            return
        if not actionable:
            return
        if mode is None:
            if actionable in ["yaml", "sbml", "omex"]:
                mode = "overwrite"
            else:
                mode = prompt_overwrite_or_append(self)
        if mode is None:
            return
        self.recent_files_manager.add_file(file_path)
        self._open_file(actionable, file_path, sep, mode)

    def _open_file(self, actionable, file_path, sep, mode):
        """Overwrites the File in the appropriate controller.

        Actionable dictates which controller to use.
        """
        if actionable == "yaml":
            self.open_yaml_and_load_files(file_path)
        elif actionable == "omex":
            self.open_omex_and_load_files(file_path)
        elif actionable == "sbml":
            self.sbml_controller.overwrite_sbml(file_path)
        elif actionable == "measurement":
            self.measurement_controller.open_table(file_path, sep, mode)
        elif actionable == "observable":
            self.observable_controller.open_table(file_path, sep, mode)
        elif actionable == "parameter":
            self.parameter_controller.open_table(file_path, sep, mode)
        elif actionable == "condition":
            self.condition_controller.open_table(file_path, sep, mode)
        elif actionable == "visualization":
            self.visualization_controller.open_table(file_path, sep, mode)
        elif actionable == "simulation":
            self.simulation_controller.open_table(file_path, sep, mode)
        elif actionable == "data_matrix":
            self.measurement_controller.process_data_matrix_file(
                file_path, mode, sep
            )

    def open_yaml_and_load_files(self, yaml_path=None, mode="overwrite"):
        """Open files from a YAML configuration.

        Opens a dialog to upload yaml file. Creates a PEtab problem and
        overwrites the current PEtab model with the new problem.
        """
        if not yaml_path:
            yaml_path, _ = QFileDialog.getOpenFileName(
                self.view, "Open YAML File", "", "YAML Files (*.yaml *.yml)"
            )
        if not yaml_path:
            return
        try:
            for controller in self.controllers:
                if controller == self.sbml_controller:
                    continue
                controller.release_completers()
            # Load the YAML content
            with open(yaml_path) as file:
                yaml_content = yaml.safe_load(file)

            if (major := get_major_version(yaml_content)) != 1:
                raise ValueError(
                    f"Only PEtab v1 problems are currently supported. "
                    f"Detected version: {major}.x."
                )

            # Resolve the directory of the YAML file to handle relative paths
            yaml_dir = Path(yaml_path).parent

            # Upload SBML model
            sbml_file_path = (
                yaml_dir / yaml_content["problems"][0]["sbml_files"][0]
            )
            self.sbml_controller.overwrite_sbml(sbml_file_path)
            self.measurement_controller.open_table(
                yaml_dir / yaml_content["problems"][0]["measurement_files"][0]
            )
            self.observable_controller.open_table(
                yaml_dir / yaml_content["problems"][0]["observable_files"][0]
            )
            self.parameter_controller.open_table(
                yaml_dir / yaml_content["parameter_file"]
            )
            self.condition_controller.open_table(
                yaml_dir / yaml_content["problems"][0]["condition_files"][0]
            )
            # Visualization is optional
            vis_path = yaml_content["problems"][0].get("visualization_files")
            if vis_path:
                self.visualization_controller.open_table(
                    yaml_dir / vis_path[0]
                )
            else:
                self.visualization_controller.clear_table()
            # Simulation should be cleared
            self.simulation_controller.clear_table()
            self.logger.log_message(
                "All files opened successfully from the YAML configuration.",
                color="green",
            )
            self.check_model()
            # rerun the completers
            for controller in self.controllers:
                if controller == self.sbml_controller:
                    continue
                controller.setup_completers()
            self.unsaved_changes_change(False)

        except Exception as e:
            self.logger.log_message(
                f"Failed to open files from YAML: {str(e)}", color="red"
            )

    def open_omex_and_load_files(self, omex_path=None):
        """Opens a petab problem from a COMBINE Archive."""
        if not omex_path:
            omex_path, _ = QFileDialog.getOpenFileName(
                self.view,
                "Open COMBINE Archive",
                "",
                "COMBINE Archive (*.omex);;All files (*)",
            )
        if not omex_path:
            return
        try:
            combine_archive = petab.problem.Problem.from_combine(omex_path)
        except Exception as e:
            self.logger.log_message(
                f"Failed to open files from OMEX: {str(e)}", color="red"
            )
            return
        # overwrite current model
        self.measurement_controller.overwrite_df(
            combine_archive.measurement_df
        )
        self.observable_controller.overwrite_df(combine_archive.observable_df)
        self.condition_controller.overwrite_df(combine_archive.condition_df)
        self.parameter_controller.overwrite_df(combine_archive.parameter_df)
        self.visualization_controller.overwrite_df(
            combine_archive.visualization_df
        )
        self.sbml_controller.overwrite_sbml(sbml_model=combine_archive.model)

    def new_file(self):
        """Empty all tables. In case of unsaved changes, ask to save."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self.view,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if reply == QMessageBox.Save:
                self.save_model()
        for controller in self.controllers:
            if controller == self.sbml_controller:
                controller.clear_model()
                continue
            controller.clear_table()
        self.view.plot_dock.plot_it()

    def check_model(self):
        """Check the consistency of the model. And log the results."""
        capture_handler = CaptureLogHandler()
        logger = logging.getLogger("petab.v1.lint")  # Target the specific
        # logger
        logger.addHandler(capture_handler)

        try:
            # Run the consistency check
            failed = self.model.test_consistency()

            # Process captured logs
            if capture_handler.records:
                captured_output = "<br>&nbsp;&nbsp;&nbsp;&nbsp;".join(
                    capture_handler.get_formatted_messages()
                )
                self.logger.log_message(
                    f"Captured petab lint logs:<br>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;{captured_output}",
                    color="purple",
                )

            # Log the consistency check result
            if not failed:
                self.logger.log_message("Model is consistent.", color="green")
                for model in self.model.pandas_models.values():
                    model.reset_invalid_cells()
            else:
                self.logger.log_message("Model is inconsistent.", color="red")
        except Exception as e:
            msg = f"PEtab linter failed at some point: {filtered_error(e)}"
            self.logger.log_message(msg, color="red")
        finally:
            # Always remove the capture handler
            logger.removeHandler(capture_handler)

    def unsaved_changes_change(self, unsaved_changes: bool):
        self.unsaved_changes = unsaved_changes
        if unsaved_changes:
            self.view.setWindowTitle(f"{self.window_title} - Unsaved Changes")
        else:
            self.view.setWindowTitle(self.window_title)

    def maybe_close(self):
        if not self.unsaved_changes:
            self.view.allow_close = True
            return
        reply = QMessageBox.question(
            self.view,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save them?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if reply == QMessageBox.Save:
            saved = self.save_model()
            self.view.allow_close = saved
        elif reply == QMessageBox.Discard:
            self.view.allow_close = True
        else:
            self.view.allow_close = False
        if self.view.allow_close:
            app = QApplication.instance()
            if app and hasattr(self, "_whats_this_filter"):
                app.removeEventFilter(self._whats_this_filter)

    def active_widget(self):
        active_widget = self.view.tab_widget.currentWidget()
        if active_widget == self.view.data_tab:
            active_widget = self.view.data_tab.focusWidget()
        if active_widget and isinstance(active_widget, QTableView):
            return active_widget
        return None

    def active_controller(self):
        active_widget = self.active_widget()
        if active_widget == self.view.measurement_dock.table_view:
            return self.measurement_controller
        if active_widget == self.view.observable_dock.table_view:
            return self.observable_controller
        if active_widget == self.view.parameter_dock.table_view:
            return self.parameter_controller
        if active_widget == self.view.condition_dock.table_view:
            return self.condition_controller
        if active_widget == self.view.visualization_dock.table_view:
            return self.visualization_controller
        if active_widget == self.view.simulation_dock.table_view:
            return self.simulation_controller
        return None

    def delete_rows(self):
        controller = self.active_controller()
        if controller:
            controller.delete_row()

    def add_row(self):
        controller = self.active_controller()
        if controller:
            controller.add_row()

    def add_column(self):
        controller = self.active_controller()
        if controller:
            controller.add_column()

    def delete_column(self):
        controller = self.active_controller()
        if controller:
            controller.delete_column()

    def clear_cells(self):
        controller = self.active_controller()
        if controller:
            controller.clear_cells()

    def filter_table(self):
        """Filter the currently activated tables."""
        filter_text = self.filter_input.text()
        for table_name, tool_button in self.filter_active.items():
            if tool_button.isChecked():
                controller = getattr(self, f"{table_name}_controller")
                controller.filter_table(filter_text)
            else:
                controller = getattr(self, f"{table_name}_controller")
                controller.remove_filter()

    def copy_to_clipboard(self):
        controller = self.active_controller()
        if controller:
            controller.copy_to_clipboard()

    def paste_from_clipboard(self):
        controller = self.active_controller()
        if controller:
            controller.paste_from_clipboard()

    def cut(self):
        controller = self.active_controller()
        if controller:
            controller.copy_to_clipboard()
            controller.clear_cells()

    def open_settings(self):
        """Opens the settings Dialogue."""
        # retrieve all current columns from the tables
        table_columns = {
            "observable": self.observable_controller.get_columns(),
            "parameter": self.parameter_controller.get_columns(),
            "measurement": self.measurement_controller.get_columns(),
            "condition": self.condition_controller.get_columns(),
            "visualization": self.visualization_controller.get_columns(),
            "simulation": self.simulation_controller.get_columns(),
        }
        settings_dialog = SettingsDialog(table_columns, self.view)
        settings_dialog.exec()

    def find(self):
        """Create a find replace bar if it is non existent."""
        if self.view.find_replace_bar is None:
            self.view.create_find_replace_bar()
        self.view.toggle_find()

    def replace(self):
        """Create a find replace bar if it is non existent."""
        if self.view.find_replace_bar is None:
            self.view.create_find_replace_bar()
        self.view.toggle_replace()

    def init_plotter(self):
        """(Re-)initialize the plotter."""
        self.view.plot_dock.initialize(
            self.measurement_controller.proxy_model,
            self.simulation_controller.proxy_model,
            self.condition_controller.proxy_model,
            self.visualization_controller.proxy_model,
            self.model,
        )
        self.plotter = self.view.plot_dock
        self.plotter.highlighter.click_callback = self._on_plot_point_clicked

    def _on_plot_point_clicked(self, x, y, label, data_type):
        # Extract observable ID from label, if formatted like 'obsId (label)'
        proxy = self.measurement_controller.proxy_model
        view = self.measurement_controller.view.table_view
        if data_type == "simulation":
            proxy = self.simulation_controller.proxy_model
            view = self.simulation_controller.view.table_view
        obs = label

        x_axis_col = "time"
        y_axis_col = data_type
        observable_col = "observableId"

        def column_index(name):
            for col in range(proxy.columnCount()):
                if proxy.headerData(col, Qt.Horizontal) == name:
                    return col
            raise ValueError(f"Column '{name}' not found.")

        x_col = column_index(x_axis_col)
        y_col = column_index(y_axis_col)
        obs_col = column_index(observable_col)

        for row in range(proxy.rowCount()):
            row_obs = proxy.index(row, obs_col).data()
            row_x = proxy.index(row, x_col).data()
            row_y = proxy.index(row, y_col).data()
            try:
                row_x, row_y = float(row_x), float(row_y)
            except ValueError:
                continue
            if row_obs == obs and row_x == x and row_y == y:
                view.selectRow(row)
                break

    def _on_table_selection_changed(self, selected, deselected):
        """Highlight the cells selected in measurement table."""
        selected_rows = get_selected(
            self.measurement_controller.view.table_view
        )
        self.plotter.highlight_from_selection(selected_rows)

    def _on_simulation_selection_changed(self, selected, deselected):
        selected_rows = get_selected(
            self.simulation_controller.view.table_view
        )
        self.plotter.highlight_from_selection(
            selected_rows,
            proxy=self.simulation_controller.proxy_model,
            y_axis_col="simulation",
        )

    def simulate(self):
        """Simulate the model."""
        # obtain petab problem
        petab_problem = self.model.current_petab_problem

        # import petabsimualtor
        import basico
        from basico.petab import PetabSimulator

        # report current basico / COPASI version
        self.logger.log_message(
            f"Simulate with basico: {basico.__version__}, COPASI: {basico.COPASI.__version__}",
            color="green",
        )

        import tempfile

        # create temp directory in temp folder:
        with tempfile.TemporaryDirectory() as temp_dir:
            # settings is only current solution statistic for now:
            settings = {"method": {"name": basico.PE.CURRENT_SOLUTION}}
            # create simulator
            simulator = PetabSimulator(
                petab_problem, settings=settings, working_dir=temp_dir
            )

            # simulate
            sim_df = simulator.simulate()

        # assign to simulation table
        self.simulation_controller.overwrite_df(sim_df)
        self.simulation_controller.model.reset_invalid_cells()

    def _schedule_plot_update(self):
        """Start the plot schedule timer."""
        self._plot_update_timer.start()

    def _toggle_whats_this_mode(self, on: bool):
        """Enable/disable click-to-help mode by installing/removing the global filter.

        On enter: show a short instruction bubble.
        """
        app = QApplication.instance()
        if not app:
            return
        if not on:
            QWhatsThis.hideText()
            try:
                QApplication.restoreOverrideCursor()
            except Exception:
                pass
            app.removeEventFilter(self._whats_this_filter)
            self.logger.log_message("Enden the Help mode.", color="blue")
            return
        # install filter
        app.installEventFilter(self._whats_this_filter)
        QApplication.setOverrideCursor(Qt.WhatsThisCursor)
        self.logger.log_message(
            "Started the Help mode. Click on any widget to see its help.",
            color="blue",
        )
        self._show_help_welcome()

    def _show_help_welcome(self):
        """Centered welcome with a 'Don't show again' option persisted in QSettings."""
        settings = settings_manager.settings
        if settings.value("help_mode/welcome_disabled", False, type=bool):
            return
        msg = QMessageBox(self.view if hasattr(self, "view") else None)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Help mode")
        msg.setTextFormat(Qt.RichText)
        msg.setText(
            "<b>Welcome to help mode</b><br>"
            "<ul>"
            "<li>Click any widget, tab, or column header to see its help.</li>"
            "<li>Click the same item again or press <b>Esc</b> to close the bubble.</li>"
            "<li>Press <b>Esc</b> with no bubble, or toggle the <i>?</i> button, to exit.</li>"
            "</ul>"
        )
        dont = QCheckBox("Don't show again")
        msg.setCheckBox(dont)
        msg.exec()
        if dont.isChecked():
            settings.setValue("help_mode/welcome_disabled", True)

    def about(self):
        """Show an about dialog."""
        repo_url = "https://github.com/PaulJonasJost/PEtab_GUI"
        config_file = settings_manager.settings.fileName()
        QMessageBox.about(
            self.view,
            "About PEtabGUI",
            f"<b>PEtabGUI</b><br>"
            f"Version: {version('petab-gui')}<br>"
            f"PEtab version: {version('petab')}<br><br>"
            f"PEtabGUI is a tool for editing and visualizing PEtab "
            f"problems.<br><br>"
            f"Visit the GitHub repository at "
            f"<a href='{repo_url}'>{repo_url}</a> "
            "for more information.<br><br>"
            f"<small>Settings are stored in "
            f"<a href='file://{config_file}'>{config_file}</a></small>",
        )
