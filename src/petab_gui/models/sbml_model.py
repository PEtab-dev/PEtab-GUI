import re

import libsbml
import petab.v1 as petab
from petab.v1.models.sbml_model import SbmlModel
from petab.v1.sbml import load_sbml_from_string
from PySide6.QtCore import QObject, QSignalBlocker, Signal

from ..C import DEFAULT_ANTIMONY_TEXT
from ..utils import antimonyToSBML, sbmlToAntimony


class SbmlViewerModel(QObject):
    """Model for the SBML viewer.

    Attributes
    ----------
    sbml_text: str
        The SBML text.
    antimony_text: str
        The SBML model converted to Antimony.
    """

    something_changed = Signal(bool)

    def __init__(self, sbml_model: petab.models.Model, parent=None):
        super().__init__(parent)
        self._sbml_model_original = sbml_model
        if sbml_model:
            self.sbml_text = libsbml.writeSBMLToString(
                self._sbml_model_original.sbml_model.getSBMLDocument()
            )
            self.antimony_text = sbmlToAntimony(self.sbml_text)
        else:
            self.antimony_text = DEFAULT_ANTIMONY_TEXT
            with QSignalBlocker(self) as blocker:
                self.convert_antimony_to_sbml()
        self.model_id = self._get_model_id()

    def convert_sbml_to_antimony(self):
        self.antimony_text = sbmlToAntimony(self.sbml_text)
        self.model_id = self._get_model_id()
        self.something_changed.emit(True)

    def convert_antimony_to_sbml(self):
        self.sbml_text = antimonyToSBML(self.antimony_text)
        self.model_id = self._get_model_id()
        self.something_changed.emit(True)

    def get_current_sbml_model(self):
        """Temporary write SBML to file and turn into petab.models.Model."""
        if self.sbml_text == "":
            return None

        sbml_reader, sbml_document, sbml_model = load_sbml_from_string(
            self.sbml_text
        )

        model_id = sbml_model.getIdAttribute()

        return SbmlModel(
            sbml_model=sbml_model,
            sbml_reader=sbml_reader,
            sbml_document=sbml_document,
            model_id=model_id,
        )

    def _get_model_id(self):
        """Extract the model ID from the SBML text."""
        document =  libsbml.readSBMLFromString(self.sbml_text)
        model = document.getModel()
        model_id = model.getIdAttribute() or "New_File"
        return model_id
