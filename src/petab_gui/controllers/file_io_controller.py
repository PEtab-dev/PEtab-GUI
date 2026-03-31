"""File I/O Controller for PEtab GUI.

This module contains the FileIOController class, which handles all
file input/output operations for PEtab models, including:
- Opening and saving PEtab YAML files
- Opening and saving COMBINE archives (OMEX)
- Opening and saving individual tables
- Exporting SBML models
- Loading example datasets
- File validation
"""

import logging
import os
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import petab.v1 as petab
import yaml
from petab.versions import get_major_version
from PySide6.QtWidgets import QFileDialog, QMessageBox

from ..settings_manager import settings_manager
from ..utils import process_file


class FileIOController:
    """Controller for file I/O operations.

    Handles all file input/output operations for the PEtab GUI, including
    loading and saving PEtab problems from various formats (YAML, OMEX, TSV).

    Attributes
    ----------
    main : MainController
        Reference to the main controller for access to models, views, and
        other controllers.
    model : PEtabModel
        The PEtab model being managed.
    view : MainWindow
        The main application window.
    logger : LoggerController
        The logger for user feedback.
    """

    def __init__(self, main_controller):
        """Initialize the FileIOController.

        Parameters
        ----------
        main_controller : MainController
            The main controller instance.
        """
        self.main = main_controller
        self.model = main_controller.model
        self.view = main_controller.view
        self.logger = main_controller.logger

    def save_model(self):
        """Save the entire PEtab model.

        Opens a dialog to select the save format and location, then saves
        the model as either a COMBINE archive (OMEX), ZIP file, or folder
        structure.

        Returns
        -------
        bool
            True if saved successfully, False otherwise.
        """
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

        # Show next steps panel if not disabled
        dont_show = settings_manager.get_value(
            "next_steps/dont_show_again", False, bool
        )
        if not dont_show:
            self.main.next_steps_panel.show_panel()

        return True

    def save_single_table(self):
        """Save the currently active table to a TSV file.

        Returns
        -------
        bool or None
            True if saved successfully, False if cancelled, None if no
            active table.
        """
        active_controller = self.main.active_controller()
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

    def save_sbml_model(self):
        """Export the SBML model to an XML file.

        Returns
        -------
        bool
            True if exported successfully, False otherwise.
        """
        if not self.model.sbml or not self.model.sbml.sbml_text:
            QMessageBox.warning(
                self.view,
                "Export SBML Model",
                "No SBML model to export.",
            )
            return False

        file_name, _ = QFileDialog.getSaveFileName(
            self.view,
            "Export SBML Model",
            f"{self.model.sbml.model_id}.xml",
            "SBML Files (*.xml *.sbml);;All Files (*)",
        )
        if not file_name:
            return False

        try:
            with open(file_name, "w") as f:
                f.write(self.model.sbml.sbml_text)
                self.logger.log_message(
                    "SBML model exported successfully to file.", color="green"
                )
            return True
        except Exception as e:
            QMessageBox.critical(
                self.view,
                "Export SBML Model",
                f"Failed to export SBML model: {e}",
            )
            return False

    def open_file(self, file_path=None, mode=None):
        """Determine appropriate course of action for a given file.

        Course of action depends on file extension, separator and header
        structure. Opens the file in the appropriate controller.

        Parameters
        ----------
        file_path : str, optional
            Path to the file to open. If None, shows a file dialog.
        mode : str, optional
            Opening mode: "overwrite" or "append". If None, prompts the user.
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
        from .utils import prompt_overwrite_or_append

        actionable, sep = process_file(file_path, self.logger)
        if actionable in ["yaml", "omex"] and mode == "append":
            self.logger.log_message(
                f"Append mode is not supported for *.{actionable} files.",
                color="red",
            )
            return
        if actionable in ["sbml"] and mode == "append":
            self.logger.log_message(
                "Append mode is not supported for SBML models.",
                color="orange",
            )
            return
        if not actionable:
            return
        if mode is None:
            if actionable in ["yaml", "sbml", "omex"]:
                mode = "overwrite"
            else:
                mode = prompt_overwrite_or_append(self.main)
        if mode is None:
            return
        self.main.recent_files_manager.add_file(file_path)
        self._open_file(actionable, file_path, sep, mode)

    def _open_file(self, actionable, file_path, sep, mode):
        """Overwrite the file in the appropriate controller.

        Actionable dictates which controller to use.

        Parameters
        ----------
        actionable : str
            Type of file: "yaml", "omex", "sbml", "measurement",
            "observable", "parameter", "condition", "visualization",
            "simulation", "data_matrix".
        file_path : str
            Path to the file.
        sep : str
            Separator used in the file (for TSV/CSV).
        mode : str
            Opening mode: "overwrite" or "append".
        """
        if actionable == "yaml":
            self.open_yaml_and_load_files(file_path)
        elif actionable == "omex":
            self.open_omex_and_load_files(file_path)
        elif actionable == "sbml":
            self.main.sbml_controller.overwrite_sbml(file_path)
        elif actionable == "measurement":
            self.main.measurement_controller.open_table(file_path, sep, mode)
        elif actionable == "observable":
            self.main.observable_controller.open_table(file_path, sep, mode)
        elif actionable == "parameter":
            self.main.parameter_controller.open_table(file_path, sep, mode)
        elif actionable == "condition":
            self.main.condition_controller.open_table(file_path, sep, mode)
        elif actionable == "visualization":
            self.main.visualization_controller.open_table(file_path, sep, mode)
        elif actionable == "simulation":
            self.main.simulation_controller.open_table(file_path, sep, mode)
        elif actionable == "data_matrix":
            self.main.measurement_controller.process_data_matrix_file(
                file_path, mode, sep
            )

    def _validate_yaml_structure(self, yaml_content):
        """Validate PEtab YAML structure before attempting to load files.

        Parameters
        ----------
        yaml_content : dict
            The parsed YAML content.

        Returns
        -------
        tuple
            (is_valid: bool, errors: list[str])
        """
        errors = []

        # Check format version
        if "format_version" not in yaml_content:
            errors.append("Missing 'format_version' field")

        # Check problems array
        if "problems" not in yaml_content:
            errors.append("Missing 'problems' field")
            return False, errors

        if (
            not isinstance(yaml_content["problems"], list)
            or not yaml_content["problems"]
        ):
            errors.append("'problems' must be a non-empty list")
            return False, errors

        problem = yaml_content["problems"][0]

        # Optional but recommended fields
        if (
            "visualization_files" not in problem
            or not problem["visualization_files"]
        ):
            errors.append("Warning: No visualization_files specified")

        # Required fields in problem
        for field in [
            "sbml_files",
            "measurement_files",
            "observable_files",
            "condition_files",
        ]:
            if field not in problem or not problem[field]:
                errors.append("Problem must contain at least one SBML file")

        # Check parameter_file (at root level)
        if "parameter_file" not in yaml_content:
            errors.append("Missing 'parameter_file' at root level")

        return len([e for e in errors if "Warning" not in e]) == 0, errors

    def _validate_files_exist(self, yaml_dir, yaml_content):
        """Validate that all files referenced in YAML exist.

        Parameters
        ----------
        yaml_dir : Path
            The directory containing the YAML file.
        yaml_content : dict
            The parsed YAML content.

        Returns
        -------
        tuple
            (all_exist: bool, missing_files: list[str])
        """
        missing_files = []
        problem = yaml_content["problems"][0]

        # Check SBML files
        for sbml_file in problem.get("sbml_files", []):
            if not (yaml_dir / sbml_file).exists():
                missing_files.append(str(sbml_file))

        # Check measurement files
        for meas_file in problem.get("measurement_files", []):
            if not (yaml_dir / meas_file).exists():
                missing_files.append(str(meas_file))

        # Check observable files
        for obs_file in problem.get("observable_files", []):
            if not (yaml_dir / obs_file).exists():
                missing_files.append(str(obs_file))

        # Check condition files
        for cond_file in problem.get("condition_files", []):
            if not (yaml_dir / cond_file).exists():
                missing_files.append(str(cond_file))

        # Check parameter file
        if "parameter_file" in yaml_content:
            param_file = yaml_content["parameter_file"]
            if not (yaml_dir / param_file).exists():
                missing_files.append(str(param_file))

        # Check visualization files (optional)
        for vis_file in problem.get("visualization_files", []):
            if not (yaml_dir / vis_file).exists():
                missing_files.append(str(vis_file))

        return len(missing_files) == 0, missing_files

    def _load_file_list(self, controller, file_list, file_type, yaml_dir):
        """Load multiple files for a given controller.

        Parameters
        ----------
        controller : object
            The controller to load files into (e.g., measurement_controller).
        file_list : list[str]
            List of file names to load.
        file_type : str
            Human-readable file type for logging (e.g., "measurement").
        yaml_dir : Path
            The directory containing the YAML and data files.
        """
        for i, file_name in enumerate(file_list):
            file_mode = "overwrite" if i == 0 else "append"
            controller.open_table(yaml_dir / file_name, mode=file_mode)
            self.logger.log_message(
                f"Loaded {file_type} file ({i + 1}/{len(file_list)}): "
                f"{file_name}",
                color="blue",
            )

    def open_yaml_and_load_files(self, yaml_path=None, mode="overwrite"):
        """Open files from a YAML configuration.

        Opens a dialog to upload YAML file. Creates a PEtab problem and
        overwrites the current PEtab model with the new problem.

        Parameters
        ----------
        yaml_path : str, optional
            Path to the YAML file. If None, shows a file dialog.
        mode : str, optional
            Opening mode (currently only "overwrite" is supported).
        """
        if not yaml_path:
            yaml_path, _ = QFileDialog.getOpenFileName(
                self.view, "Open YAML File", "", "YAML Files (*.yaml *.yml)"
            )
        if not yaml_path:
            return
        try:
            for controller in self.main.controllers:
                if controller == self.main.sbml_controller:
                    continue
                controller.release_completers()

            # Load the YAML content
            with open(yaml_path, encoding="utf-8") as file:
                yaml_content = yaml.safe_load(file)

            # Validate PEtab version
            if (major := get_major_version(yaml_content)) != 1:
                raise ValueError(
                    f"Only PEtab v1 problems are currently supported. "
                    f"Detected version: {major}.x."
                )

            # Validate YAML structure
            is_valid, errors = self._validate_yaml_structure(yaml_content)
            if not is_valid:
                error_msg = "Invalid YAML structure:\n  - " + "\n  - ".join(
                    [e for e in errors if "Warning" not in e]
                )
                self.logger.log_message(error_msg, color="red")
                QMessageBox.critical(
                    self.view, "Invalid PEtab YAML", error_msg
                )
                return

            # Log warnings but continue
            warnings = [e for e in errors if "Warning" in e]
            for warning in warnings:
                self.logger.log_message(warning, color="orange")

            # Resolve the directory of the YAML file to handle relative paths
            yaml_dir = Path(yaml_path).parent

            # Validate file existence
            all_exist, missing_files = self._validate_files_exist(
                yaml_dir, yaml_content
            )
            if not all_exist:
                error_msg = (
                    "The following files referenced in the YAML are "
                    "missing:\n  - " + "\n  - ".join(missing_files)
                )
                self.logger.log_message(error_msg, color="red")
                QMessageBox.critical(self.view, "Missing Files", error_msg)
                return

            problem = yaml_content["problems"][0]

            # Load SBML model (required, single file)
            sbml_files = problem.get("sbml_files", [])
            if sbml_files:
                sbml_file_path = yaml_dir / sbml_files[0]
                self.main.sbml_controller.overwrite_sbml(sbml_file_path)
                self.logger.log_message(
                    f"Loaded SBML file: {sbml_files[0]}", color="blue"
                )

            # Load measurement files (multiple allowed)
            measurement_files = problem.get("measurement_files", [])
            if measurement_files:
                self._load_file_list(
                    self.main.measurement_controller,
                    measurement_files,
                    "measurement",
                    yaml_dir,
                )

            # Load observable files (multiple allowed)
            observable_files = problem.get("observable_files", [])
            if observable_files:
                self._load_file_list(
                    self.main.observable_controller,
                    observable_files,
                    "observable",
                    yaml_dir,
                )

            # Load condition files (multiple allowed)
            condition_files = problem.get("condition_files", [])
            if condition_files:
                self._load_file_list(
                    self.main.condition_controller,
                    condition_files,
                    "condition",
                    yaml_dir,
                )

            # Load parameter file (required, single file at root level)
            if "parameter_file" in yaml_content:
                param_file = yaml_content["parameter_file"]
                self.main.parameter_controller.open_table(
                    yaml_dir / param_file
                )
                self.logger.log_message(
                    f"Loaded parameter file: {param_file}", color="blue"
                )

            # Load visualization files (optional, multiple allowed)
            visualization_files = problem.get("visualization_files", [])
            if visualization_files:
                self._load_file_list(
                    self.main.visualization_controller,
                    visualization_files,
                    "visualization",
                    yaml_dir,
                )
            else:
                self.main.visualization_controller.clear_table()

            # Simulation should be cleared
            self.main.simulation_controller.clear_table()

            self.logger.log_message(
                "All files opened successfully from the YAML configuration.",
                color="green",
            )
            self.main.validation.check_model()

            # Rerun the completers
            for controller in self.main.controllers:
                if controller == self.main.sbml_controller:
                    continue
                controller.setup_completers()
            self.main.unsaved_changes_change(False)

        except FileNotFoundError as e:
            error_msg = (
                f"File not found: "
                f"{e.filename if hasattr(e, 'filename') else str(e)}"
            )
            self.logger.log_message(error_msg, color="red")
            QMessageBox.warning(self.view, "File Not Found", error_msg)
        except KeyError as e:
            error_msg = f"Missing required field in YAML: {str(e)}"
            self.logger.log_message(error_msg, color="red")
            QMessageBox.warning(self.view, "Invalid YAML", error_msg)
        except ValueError as e:
            error_msg = f"Invalid YAML structure: {str(e)}"
            self.logger.log_message(error_msg, color="red")
            QMessageBox.warning(self.view, "Invalid YAML", error_msg)
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error: {str(e)}"
            self.logger.log_message(error_msg, color="red")
            QMessageBox.warning(self.view, "YAML Parsing Error", error_msg)
        except Exception as e:
            error_msg = f"Unexpected error loading YAML: {str(e)}"
            self.logger.log_message(error_msg, color="red")
            logging.exception("Full traceback for YAML loading error:")
            QMessageBox.critical(self.view, "Error", error_msg)

    def open_omex_and_load_files(self, omex_path=None):
        """Open a PEtab problem from a COMBINE Archive.

        Parameters
        ----------
        omex_path : str, optional
            Path to the OMEX file. If None, shows a file dialog.
        """
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
        self.main.measurement_controller.overwrite_df(
            combine_archive.measurement_df
        )
        self.main.observable_controller.overwrite_df(
            combine_archive.observable_df
        )
        self.main.condition_controller.overwrite_df(
            combine_archive.condition_df
        )
        self.main.parameter_controller.overwrite_df(
            combine_archive.parameter_df
        )
        self.main.visualization_controller.overwrite_df(
            combine_archive.visualization_df
        )
        self.main.sbml_controller.overwrite_sbml(
            sbml_model=combine_archive.model
        )

    def new_file(self):
        """Empty all tables.

        In case of unsaved changes, asks the user whether to save.
        """
        if self.main.unsaved_changes:
            reply = QMessageBox.question(
                self.view,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if reply == QMessageBox.Save:
                self.save_model()
        for controller in self.main.controllers:
            if controller == self.main.sbml_controller:
                controller.clear_model()
                continue
            controller.clear_table()
        self.view.plot_dock.plot_it()
        self.main.unsaved_changes_change(False)

    def load_example(self, example_name):
        """Load an internal example PEtab problem.

        Parameters
        ----------
        example_name : str
            Name of the example subdirectory (e.g., "Boehm",
            "Simple_Conversion").

        Notes
        -----
        Finds and loads the example dataset from the package directory.
        No internet connection required - the example is bundled with the
        package.
        """
        try:
            # Use importlib.resources to access packaged example files
            from importlib.resources import as_file, files

            example_files = files("petab_gui.example")

            # Check if the example package exists
            if not example_files.is_dir():
                error_msg = (
                    "Could not find the example dataset. "
                    "The example folder may not be properly installed."
                )
                self.logger.log_message(error_msg, color="red")
                QMessageBox.warning(self.view, "Example Not Found", error_msg)
                return

            # Get the problem.yaml file path for the specified example
            yaml_file = example_files.joinpath(example_name, "problem.yaml")

            with as_file(yaml_file) as yaml_path:
                if not yaml_path.exists():
                    error_msg = (
                        f"Example '{example_name}' not found or "
                        f"problem.yaml file is missing."
                    )
                    self.logger.log_message(error_msg, color="red")
                    QMessageBox.warning(
                        self.view, "Example Invalid", error_msg
                    )
                    return

                # Load the example
                self.logger.log_message(
                    f"Loading '{example_name}' example dataset...",
                    color="blue",
                )
                self.open_yaml_and_load_files(str(yaml_path))

        except ModuleNotFoundError as e:
            error_msg = (
                "Example dataset not found. It may not be installed properly. "
                f"Error: {str(e)}"
            )
            self.logger.log_message(error_msg, color="red")
            QMessageBox.warning(self.view, "Example Not Found", error_msg)
        except Exception as e:
            error_msg = f"Failed to load example: {str(e)}"
            self.logger.log_message(error_msg, color="red")
            QMessageBox.critical(self.view, "Error Loading Example", error_msg)

    def get_current_problem(self):
        """Get the current PEtab problem from the model.

        Returns
        -------
        petab.Problem
            The current PEtab problem.
        """
        return self.model.current_petab_problem
