"""Class for handling SBML files in the GUI."""

from pathlib import Path

import libsbml
from petab.models.sbml_model import SbmlModel
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog

from ..C import DEFAULT_ANTIMONY_TEXT
from ..models.sbml_model import SbmlViewerModel
from ..utils import sbmlToAntimony
from ..views.sbml_view import SbmlViewer


class SbmlController(QObject):
    """Class for handling SBML files in the GUI."""

    overwritten_model = Signal()

    def __init__(
        self,
        view: SbmlViewer,
        model: SbmlViewerModel,
        logger,
        mother_controller,
    ):
        """Initialize the SBML controller.

        Parameters
        ----------
        view: QAbstractItemView
            The view of the SBML table.
        model: SbmlModel
            The model of the SBML table.
        logger:
            Handles all logging tasks
        mother_controller: MainController
            The main controller of the application. Needed for signal
            forwarding.
        """
        super().__init__()
        self.view = view
        self.model = model
        self.logger = logger
        self.mother_controller = mother_controller
        # set the texts once
        self.view.sbml_text_edit.setPlainText(self.model.sbml_text)
        self.view.antimony_text_edit.setPlainText(self.model.antimony_text)
        self.setup_connections()

    def setup_connections(self):
        """Setup all connections for the SBML controller."""
        self.view.forward_sbml_button.clicked.connect(
            self.update_antimony_from_sbml
        )
        self.view.forward_antimony_button.clicked.connect(
            self.update_sbml_from_antimony
        )

    def reset_to_original_model(self):
        """Reset the model to the original SBML and Antimony text."""
        self.logger.log_message(
            "Resetting the model to the original SBML and Antimony text",
            color="orange",
        )
        self.model.sbml_text = libsbml.writeSBMLToString(
            self.model._sbml_model_original.sbml_model.getSBMLDocument()
        )
        self.model.antimony_text = sbmlToAntimony(self.model.sbml_text)
        self.view.sbml_text_edit.setPlainText(self.model.sbml_text)
        self.view.antimony_text_edit.setPlainText(self.model.antimony_text)

    def update_antimony_from_sbml(self):
        """Convert current SBML to Antimony and update the Antimony text."""
        self.model.sbml_text = self.view.sbml_text_edit.toPlainText()
        try:
            self.model.convert_sbml_to_antimony()
        except Exception as e:
            self.logger.log_message(
                f"Failed to convert SBML to Antimony: {str(e)}", color="red"
            )
            return
        self.logger.log_message("Converting SBML to Antimony", color="green")
        self.view.antimony_text_edit.setPlainText(self.model.antimony_text)
        self.model.something_changed.emit(True)

    def update_sbml_from_antimony(self):
        """Convert current Antimony to SBML and update the SBML text."""
        self.model.antimony_text = self.view.antimony_text_edit.toPlainText()
        try:
            self.model.convert_antimony_to_sbml()
        except Exception as e:
            self.logger.log_message(
                f"Failed to convert Antimony to SBML: {str(e)}", color="red"
            )
            return
        self.logger.log_message("Converting Antimony to SBML", color="green")
        self.view.sbml_text_edit.setPlainText(self.model.sbml_text)
        self.model.something_changed.emit(True)

    def overwrite_sbml(self, file_path=None, sbml_model=None):
        """
        Overwrite the existing SBML model.

        Parameters
        ----------
        file_path: str, optional
            Path to the SBML file to open.
            If None, a file dialog will be opened
        sbml_model: SbmlModel, optional
            An SbmlModel instance to use directly.
            If provided, file_path will be ignored.
        """
        if sbml_model:
            self.model._sbml_model_original = sbml_model
            self._overwrite_sbml_with_model(sbml_model)
            return
        if not file_path:
            # Open a file dialog to select an SBML file
            file_path, _ = QFileDialog.getOpenFileName(
                self.view, "Open SBML File", "", "SBML Files (*.xml *.sbml)"
            )
        if not file_path:
            return
        try:
            new_sbml_model = SbmlModel.from_file(Path(file_path))
        except Exception as e:
            self.logger.log_message(
                f"Failed to open SBML file: {str(e)}", color="red"
            )
            return
        self.model._sbml_model_original = new_sbml_model
        self._overwrite_sbml_with_model(new_sbml_model)

    def _overwrite_sbml_with_model(self, sbml_model: SbmlModel):
        """Overwrite the existing SBML model with a given SbmlModel instance.

        Parameters
        ----------
        sbml_model: SbmlModel
            The SbmlModel instance to use.
        """
        self.model.sbml_text = sbml_model.to_sbml_str()
        self.model.convert_sbml_to_antimony()
        self.view.sbml_text_edit.setPlainText(self.model.sbml_text)
        self.view.antimony_text_edit.setPlainText(self.model.antimony_text)

        self.overwritten_model.emit()
        self.logger.log_message(
            "SBML model successfully overwritten.", color="green"
        )

    def clear_model(self):
        """Clear the model in case the user wants to start a new problem."""
        self.model.antimony_text = DEFAULT_ANTIMONY_TEXT
        self.model.convert_antimony_to_sbml()
        self.view.sbml_text_edit.setPlainText(self.model.sbml_text)
        self.view.antimony_text_edit.setPlainText(self.model.antimony_text)
        self.overwritten_model.emit()
