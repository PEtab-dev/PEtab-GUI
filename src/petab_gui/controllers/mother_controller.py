from PySide6.QtWidgets import QMessageBox, QFileDialog, QLineEdit, QWidget, \
    QHBoxLayout, QToolButton, QTableView
from PySide6.QtGui import QShortcut, QKeySequence, QAction
import zipfile
import tempfile
import os
from io import BytesIO, StringIO
import logging
import yaml
import qtawesome as qta
from ..utils import FindReplaceDialog, CaptureLogHandler
from PySide6.QtCore import Qt
from pathlib import Path
from ..models import PEtabModel
from .sbml_controller import SbmlController
from .table_controllers import MeasurementController, ObservableController, \
    ConditionController, ParameterController
from .logger_controller import LoggerController
from ..views import TaskBar


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
        self.setup_edit_menu()


    def setup_task_bar(self):
        """Create shortcuts for the main window."""
        self.view.task_bar = TaskBar(self.view, self.actions)
        self.task_bar = self.view.task_bar


    # CONNECTIONS
    def setup_edit_menu(self):
        """Create connections for the Edit menu actions in task bar."""
        edit_menu = self.task_bar.edit_menu
        # Find and Replace
        edit_menu.find_replace_action.triggered.connect(
            self.open_find_replace_dialog
        )
        # Add columns
        edit_menu.add_c_meas_action.triggered.connect(
            self.measurement_controller.add_column
        )
        edit_menu.add_c_obs_action.triggered.connect(
            self.observable_controller.add_column
        )
        edit_menu.add_c_para_action.triggered.connect(
            self.parameter_controller.add_column
        )
        edit_menu.add_c_cond_action.triggered.connect(
            self.condition_controller.add_column
        )


    def setup_connections(self):
        """Setup connections.

        Sets all connections that communicate from one different
        Models/Views/Controllers to another. Also sets general connections.
        """
        # Rename Observable
        self.observable_controller.observable_2be_renamed.connect(
            self.measurement_controller.rename_observable
        )
        # Add new observable
        self.model.measurement.observable_id_changed.connect(
            self.observable_controller.maybe_add_observable
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
        # Closing event
        self.view.closing_signal.connect(
            self.maybe_close
        )
        # Lint Problem
        for view in self.logger.views:
            view.lint_model_button.clicked.connect(
                self.model.test_consistency
            )

    def setup_actions(self):
        """Setup actions for the main controller."""
        actions = {}
        # Open YAML
        actions["open_yaml"] = QAction(
            qta.icon("mdi6.folder-open"),
            "Open YAML Configuration", self.view
        )
        actions["open_yaml"].triggered.connect(self.open_yaml_and_load_files)
        # Save
        actions["save"] = QAction(
            qta.icon("mdi6.content-save-all"),
            "Save", self.view
        )
        actions["save"].setShortcut("Ctrl+S")
        actions["save"].triggered.connect(self.save_model)
        # Find + Replace
        actions["find+replace"] = QAction(
            qta.icon("mdi6.find-replace"),
            "Find/Replace", self.view
        )
        actions["find+replace"].setShortcut("Ctrl+R")
        actions["find+replace"].triggered.connect(self.open_find_replace_dialog)
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
        # TODO: fix add row and delete row
        # check petab model
        actions["check_petab"] = QAction(
            qta.icon("mdi6.checkbox-multiple-marked-circle-outline"),
            "Check PEtab", self.view
        )
        actions["check_petab"].triggered.connect(self.check_model)

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
            return None
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
                "y": self.model.measurement._data_frame.iloc[row]["measurement"]
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

    def open_file(self, file_path=None):
        """Opens PEtab files (.yaml) or SBML files (.xml .sbml)."""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self.view,
                "Open File",
                "",
                "PEtab Files (*.yaml *.yml);;SBML Files (*.xml *.sbml)"
            )
        if not file_path:
            return
        if file_path.endswith((".yaml", ".yml")):
            self.open_yaml_and_load_files(file_path)
        elif file_path.endswith((".xml", ".sbml")):
            self.sbml_controller.open_and_overwrite_sbml(file_path)


    def open_yaml_and_load_files(self, yaml_path=None):
        """Upload files from a YAML configuration.

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
            # Load the YAML content
            with open(yaml_path, 'r') as file:
                yaml_content = yaml.safe_load(file)

            # Resolve the directory of the YAML file to handle relative paths
            yaml_dir = Path(yaml_path).parent

            # Upload SBML model
            sbml_file_path = \
                yaml_dir / yaml_content['problems'][0]['sbml_files'][0]
            self.sbml_controller.open_and_overwrite_sbml(sbml_file_path)
            self.measurement_controller.open_and_overwrite_table(
                yaml_dir / yaml_content['problems'][0]['measurement_files'][0]
            )
            self.observable_controller.open_and_overwrite_table(
                yaml_dir / yaml_content['problems'][0]['observable_files'][0]
            )
            self.parameter_controller.open_and_overwrite_table(
                yaml_dir / yaml_content['parameter_file']
            )
            self.condition_controller.open_and_overwrite_table(
                yaml_dir / yaml_content['problems'][0]['condition_files'][0]
            )
            self.logger.log_message(
                "All files uploaded successfully from the YAML configuration.",
                color="green"
            )
            # rerun the completers
            for controller in [
                self.measurement_controller,
                self.observable_controller,
                self.parameter_controller,
                self.condition_controller
            ]:
                controller.setup_completers()
            self.unsaved_changes = False

        except Exception as e:
            self.logger.log_message(
                f"Failed to upload files from YAML: {str(e)}", color="red"
            )

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
            self.save_model()
            self.view.allow_close = True
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
        else:
            print("No active controller found")

    def add_row(self):
        controller = self.active_controller()
        if controller:
            controller.add_row()
        else:
            print("No active controller found")
