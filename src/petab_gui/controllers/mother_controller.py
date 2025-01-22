from functools import partial

from PySide6.QtWidgets import QMessageBox, QFileDialog, QLineEdit, QWidget, \
    QHBoxLayout, QToolButton, QTableView
from PySide6.QtGui import QAction
import zipfile
import tempfile
import os
from io import BytesIO
import logging
import yaml
import qtawesome as qta
from ..utils import FindReplaceDialog, CaptureLogHandler, process_file
from PySide6.QtCore import Qt
from pathlib import Path
from ..models import PEtabModel
from .sbml_controller import SbmlController
from .table_controllers import MeasurementController, ObservableController, \
    ConditionController, ParameterController
from .logger_controller import LoggerController
from ..views import TaskBar
from .utils import prompt_overwrite_or_append
from functools import partial


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
        self.task_bar = None
        self.view = view
        self.model = model
        self.logger = LoggerController(view.logger_views)
        # CONTROLLERS
        self.measurement_controller = MeasurementController(
            self.view.measurement_dock,
            self.model.measurement,
            self.logger,
            self
        )
        self.observable_controller = ObservableController(
            self.view.observable_dock,
            self.model.observable,
            self.logger,
            self
        )
        self.parameter_controller = ParameterController(
            self.view.parameter_dock,
            self.model.parameter,
            self.logger,
            self
        )
        self.condition_controller = ConditionController(
            self.view.condition_dock,
            self.model.condition,
            self.logger,
            self
        )
        self.sbml_controller = SbmlController(
            self.view.sbml_viewer,
            self.model.sbml,
            self.logger,
            self
        )
        self.controllers = [
            self.measurement_controller,
            self.observable_controller,
            self.parameter_controller,
            self.condition_controller,
            self.sbml_controller
        ]
        # Checkbox states for Find + Replace
        self.petab_checkbox_states = {
            "measurement": False,
            "observable": False,
            "parameter": False,
            "condition": False
        }
        self.sbml_checkbox_states = {
            "sbml": False,
            "antimony": False
        }
        self.unsaved_changes = False
        self.filter = QLineEdit()
        self.filter_active = {}  # Saves which tables the filter applies to
        self.actions = self.setup_actions()
        self.view.setup_toolbar(self.actions)

        self.setup_connections()
        self.setup_task_bar()

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
                column_names = "observableId"
            )
        )
        # Rename Condition
        self.condition_controller.condition_2be_renamed.connect(
            partial(
                self.measurement_controller.rename_value,
                column_names = ["simulationConditionId",
                "preequilibrationConditionId"]
            )
        )
        # Add new condition or observable
        self.model.measurement.relevant_id_changed.connect(
            lambda x, y, z: self.observable_controller.maybe_add_observable(
                x, y) if z == "observable" else
            self.condition_controller.maybe_add_condition(
                x, y) if z == "condition" else None
        )
        # Maybe Move to a Plot Model
        self.view.measurement_dock.table_view.selectionModel().selectionChanged.connect(
            self.handle_selection_changed
        )
        self.model.measurement.dataChanged.connect(
            self.handle_data_changed
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
        self.model.sbml.something_changed.connect(
            self.unsaved_changes_change
        )
        # correctly update the visibility even when "x" is clicked in a dock
        self.view.measurement_dock.visibilityChanged.connect(
            lambda visible: self.actions["show_measurement"].setChecked(
                visible)
        )
        self.view.observable_dock.visibilityChanged.connect(
            lambda visible: self.actions["show_observable"].setChecked(visible)
        )
        self.view.parameter_dock.visibilityChanged.connect(
            lambda visible: self.actions["show_parameter"].setChecked(visible)
        )
        self.view.condition_dock.visibilityChanged.connect(
            lambda visible: self.actions["show_condition"].setChecked(visible)
        )
        self.view.logger_dock.visibilityChanged.connect(
            lambda visible: self.actions["show_logger"].setChecked(visible)
        )
        self.view.plot_dock.visibilityChanged.connect(
            lambda visible: self.actions["show_plot"].setChecked(visible)
        )

    def setup_actions(self):
        """Setup actions for the main controller."""
        actions = {"close": QAction(
            qta.icon("mdi6.close"),
            "&Close", self.view
        )}
        # Close
        actions["close"].setShortcut("Ctrl+Q")
        actions["close"].triggered.connect(self.view.close)
        # New File
        actions["new"] = QAction(
            qta.icon("mdi6.file-document"),
            "&New", self.view
        )
        actions["new"].setShortcut("Ctrl+N")
        actions["new"].triggered.connect(self.new_file)
        # Open File
        actions["open"] = QAction(
            qta.icon("mdi6.folder-open"),
            "&Open", self.view
        )
        actions["open"].setShortcut("Ctrl+O")
        actions["open"].triggered.connect(
            partial(self.open_file, mode="overwrite")
        )
        # Add File
        actions["add"] = QAction(
            qta.icon("mdi6.table-plus"),
            "Add", self.view
        )
        actions["add"].setShortcut("Ctrl+Shift+O")
        actions["add"].triggered.connect(
            partial(self.open_file, mode="append")
        )
        # Save
        actions["save"] = QAction(
            qta.icon("mdi6.content-save-all"),
            "&Save", self.view
        )
        actions["save"].setShortcut("Ctrl+S")
        actions["save"].triggered.connect(self.save_model)
        # Find + Replace
        actions["find+replace"] = QAction(
            qta.icon("mdi6.find-replace"),
            "Find/Replace", self.view
        )
        actions["find+replace"].setShortcut("Ctrl+R")
        actions["find+replace"].triggered.connect(
            self.open_find_replace_dialog)
        # add/delete row
        actions["add_row"] = QAction(
            qta.icon("mdi6.table-row-plus-after"),
            "Add Row", self.view
        )
        actions["add_row"].triggered.connect(self.add_row)
        actions["delete_row"] = QAction(
            qta.icon("mdi6.table-row-remove"),
            "Delete Row(s)", self.view
        )
        actions["delete_row"].triggered.connect(self.delete_rows)
        # add/delete column
        actions["add_column"] = QAction(
            qta.icon("mdi6.table-column-plus-after"),
            "Add Column", self.view
        )
        actions["add_column"].triggered.connect(self.add_column)
        actions["delete_column"] = QAction(
            qta.icon("mdi6.table-column-remove"),
            "Delete Column(s)", self.view
        )
        actions["delete_column"].triggered.connect(self.delete_column)
        # check petab model
        actions["check_petab"] = QAction(
            qta.icon("mdi6.checkbox-multiple-marked-circle-outline"),
            "Check PEtab", self.view
        )
        actions["check_petab"].triggered.connect(self.check_model)
        actions["reset_model"] = QAction(
            qta.icon("mdi6.restore"),
            "Reset SBML Model", self.view
        )
        actions["reset_model"].triggered.connect(
            self.sbml_controller.reset_to_original_model
        )

        # Filter widget
        filter_widget = QWidget()
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_widget.setLayout(filter_layout)
        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Filter not functional yet ...")
        filter_layout.addWidget(filter_input)
        for table_n, table_name in zip(
            ["m", "p", "o", "c", "x"],
            ["Measurement", "Parameter", "Observable", "Condition", "SBML"]
        ):
            tool_button = QToolButton()
            icon = qta.icon(
                "mdi6.alpha-{}".format(table_n), "mdi6.filter",
                options=[
                    {'scale_factor': 1.5, 'offset': (-0.2, -0.2)},
                    {'off': 'mdi6.filter-off', 'offset': (0.3, 0.3)},
                ],
            )
            tool_button.setIcon(icon)
            tool_button.setCheckable(True)
            tool_button.setToolTip(f"Filter for {table_name}")
            filter_layout.addWidget(tool_button)
            self.filter_active[table_name] = tool_button
        actions["filter_widget"] = filter_widget

        # show/hide elements
        for element in ["measurement", "observable", "parameter", "condition"]:
            actions[f"show_{element}"] = QAction(
                f"{element.capitalize()} Table", self.view
            )
            actions[f"show_{element}"].setCheckable(True)
            actions[f"show_{element}"].setChecked(True)
        actions["show_logger"] = QAction(
            "Info", self.view
        )
        actions["show_logger"].setCheckable(True)
        actions["show_logger"].setChecked(True)
        actions["show_plot"] = QAction(
            "Data Plot", self.view
        )
        actions["show_plot"].setCheckable(True)
        actions["show_plot"].setChecked(True)
        # connect actions
        actions["show_measurement"].toggled.connect(
            lambda checked: self.view.measurement_dock.setVisible(checked)
        )
        actions["show_observable"].toggled.connect(
            lambda checked: self.view.observable_dock.setVisible(checked)
        )
        actions["show_parameter"].toggled.connect(
            lambda checked: self.view.parameter_dock.setVisible(checked)
        )
        actions["show_condition"].toggled.connect(
            lambda checked: self.view.condition_dock.setVisible(checked)
        )
        actions["show_logger"].toggled.connect(
            lambda checked: self.view.logger_dock.setVisible(checked)
        )
        actions["show_plot"].toggled.connect(
            lambda checked: self.view.plot_dock.setVisible(checked)
        )

        return actions

    def save_model(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self.view,
            "Save Project",
            "",
            "Zip Files (*.zip)",
            options=options
        )
        if not file_name:
            return False
        if not file_name.endswith(".zip"):
            file_name += ".zip"

        # Create a temporary directory to save the model's files
        with tempfile.TemporaryDirectory() as temp_dir:
            self.model.save(temp_dir)

            # Create a bytes buffer to hold the zip file in memory
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                # Add files to zip archive
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        with open(file_path, 'rb') as f:
                            zip_file.writestr(file, f.read())
            with open(file_name, 'wb') as f:
                f.write(buffer.getvalue())

        QMessageBox.information(
            self.view, "Save Project",
            f"Project saved successfully to {file_name}"
        )
        return True

    def open_find_replace_dialog(self):
        current_tab = self.view.tab_widget.currentIndex()
        if current_tab == 0:
            # TODO: rewrite functionality in FindReplaceDialoge
            dialog = FindReplaceDialog(
                self.view, mode="petab",
                checkbox_states=self.petab_checkbox_states,
                controller=self
            )
        elif current_tab == 1:
            dialog = FindReplaceDialog(
                self.view, mode="sbml",
                checkbox_states=self.sbml_checkbox_states,
                controller=self
            )
        dialog.exec()

    def handle_selection_changed(self):
        # ??
        self.update_plot()

    def handle_data_changed(self, top_left, bottom_right, roles):
        # ??
        if not roles or Qt.DisplayRole in roles:
            self.update_plot()

    def update_plot(self):
        # ??
        selection_model = \
            self.view.measurement_dock.table_view.selectionModel()
        indexes = selection_model.selectedIndexes()
        if not indexes:
            return None

        selected_points = {}
        for index in indexes:
            if index.row() == self.model.measurement.get_df().shape[0]:
                continue
            row = index.row()
            observable_id = self.model.measurement._data_frame.iloc[row][
                "observableId"]
            if observable_id not in selected_points:
                selected_points[observable_id] = []
            selected_points[observable_id].append({
                "x": self.model.measurement._data_frame.iloc[row]["time"],
                "y": self.model.measurement._data_frame.iloc[row][
                    "measurement"]
            })
        if selected_points == {}:
            return None

        measurement_data = self.model.measurement._data_frame
        plot_data = {
            "all_data": [],
            "selected_points": selected_points
        }
        for observable_id in selected_points.keys():
            observable_data = measurement_data[
                measurement_data["observableId"] == observable_id]
            plot_data["all_data"].append({
                "observable_id": observable_id,
                "x": observable_data["time"].tolist(),
                "y": observable_data["measurement"].tolist()
            })

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
                "All supported (*.yaml *.yml *.xml *.sbml *.tsv *.csv *.txt);;"
                "PEtab Problems (*.yaml *.yml);;SBML Files (*.xml *.sbml);;"
                "PEtab Tables or Data Matrix (*.tsv *.csv *.txt);;"
                "All files (*)"
            )
        if not file_path:
            return
        # handle file appropriately
        actionable, sep = process_file(file_path, self.logger)
        if actionable in ["yaml", "sbml"] and mode == "append":
            self.logger.log_message(
                f"Append mode is not supported for *.{actionable} files.",
                color="red"
            )
            return
        if not actionable:
            return
        if mode is None:
            if actionable in ["yaml", "sbml"]:
                mode = "overwrite"
            else:
                mode = prompt_overwrite_or_append(self)
        if mode is None:
            return
        self._open_file(actionable, file_path, sep, mode)

    def _open_file(self, actionable, file_path, sep, mode):
        """Overwrites the File in the appropriate controller.
        Actionable dictates which controller to use.
        """
        if actionable == "yaml":
            self.open_yaml_and_load_files(file_path)
        elif actionable == "sbml":
            self.sbml_controller.overwrite_sbml(file_path)
        elif actionable == "measurement":
            self.measurement_controller.open_table(
                file_path, sep, mode
            )
        elif actionable == "observable":
            self.observable_controller.open_table(
                file_path, sep, mode
            )
        elif actionable == "parameter":
            self.parameter_controller.open_table(
                file_path, sep, mode
            )
        elif actionable == "condition":
            self.condition_controller.open_table(
                file_path, sep, mode
            )
        elif actionable == "data_matrix":
            self.measurement_controller.process_data_matrix_file(
                file_path, sep, mode
            )

    def open_yaml_and_load_files(self, yaml_path=None, mode="overwrite"):
        """Open files from a YAML configuration.

        Opens a dialog to upload yaml file. Creates a PEtab problem and
        overwrites the current PEtab model with the new problem.
        """
        if not yaml_path:
            yaml_path, _ = QFileDialog.getOpenFileName(
                self.view,
                "Open YAML File",
                "",
                "YAML Files (*.yaml *.yml)"
            )
        if not yaml_path:
            return
        try:
            for controller in self.controllers:
                if controller == self.sbml_controller:
                    continue
                controller.release_completers()
            # Load the YAML content
            with open(yaml_path, 'r') as file:
                yaml_content = yaml.safe_load(file)

            # Resolve the directory of the YAML file to handle relative paths
            yaml_dir = Path(yaml_path).parent

            # Upload SBML model
            sbml_file_path = \
                yaml_dir / yaml_content['problems'][0]['sbml_files'][0]
            self.sbml_controller.overwrite_sbml(sbml_file_path)
            self.measurement_controller.open_table(
                yaml_dir / yaml_content['problems'][0]['measurement_files'][0]
            )
            self.observable_controller.open_table(
                yaml_dir / yaml_content['problems'][0]['observable_files'][0]
            )
            self.parameter_controller.open_table(
                yaml_dir / yaml_content['parameter_file']
            )
            self.condition_controller.open_table(
                yaml_dir / yaml_content['problems'][0]['condition_files'][0]
            )
            self.logger.log_message(
                "All files opened successfully from the YAML configuration.",
                color="green"
            )
            # rerun the completers
            for controller in self.controllers:
                if controller == self.sbml_controller:
                    continue
                controller.setup_completers()
            self.unsaved_changes = False

        except Exception as e:
            self.logger.log_message(
                f"Failed to open files from YAML: {str(e)}", color="red"
            )

    def new_file(self):
        """Empty all tables. In case of unsaved changes, ask to save."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self.view, "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                self.save_model()
        for controller in [
            self.measurement_controller,
            self.observable_controller,
            self.parameter_controller,
            self.condition_controller
        ]:
            controller.clear_table()

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
                    color="purple"
                )

            # Log the consistency check result
            if not failed:
                self.logger.log_message("Model is consistent.", color="green")
                for model in self.model.pandas_models.values():
                    model.reset_invalid_cells()
            else:
                self.logger.log_message("Model is inconsistent.", color="red")
        finally:
            # Always remove the capture handler
            logger.removeHandler(capture_handler)

    def unsaved_changes_change(self, unsaved_changes: bool):
        self.unsaved_changes = unsaved_changes
        if unsaved_changes:
            self.view.setWindowTitle("PEtab Editor - Unsaved Changes")
        else:
            self.view.setWindowTitle("PEtab Editor")

    def maybe_close(self):
        if not self.unsaved_changes:
            self.view.allow_close = True
            return
        reply = QMessageBox.question(
            self.view, "Unsaved Changes",
            "You have unsaved changes. Do you want to save them?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        if reply == QMessageBox.Save:
            saved = self.save_model()
            self.view.allow_close = saved
        elif reply == QMessageBox.Discard:
            self.view.allow_close = True
        else:
            self.view.allow_close = False

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
        print("No active controller found")
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
