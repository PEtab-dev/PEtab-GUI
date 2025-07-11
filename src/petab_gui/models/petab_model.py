"""Contains the overarching PEtab model class."""

from __future__ import annotations

from pathlib import Path
import tempfile

import petab.v1 as petab

from .pandas_table_model import (
    ConditionModel,
    MeasurementModel,
    ObservableModel,
    ParameterModel,
    VisualizationModel,
)
from .sbml_model import SbmlViewerModel


class PEtabModel:
    """PEtab model class.

    This class is responsible for managing the petab Problem, is a container
    for the different data models used in the application and provides
    functionality to test the consistency of the data.

    Attributes
    ----------
    problem: petab.Problem
        The PEtab problem.
    measurement_model: PandasTableModel
        The measurement data model.
    observable_model: PandasTableModel
        The observable data model.
    parameter_model: PandasTableModel
        The parameter data model.
    condition_model: PandasTableModel
        The condition data model.
    sbml_model: SbmlModel
        The SBML model.
    controller: Controller
        The controller of the application.
    """

    def __init__(
        self,
        petab_problem: petab.Problem | None = None,
    ):
        """Initialize the PEtab model.

        Parameters
        ----------
        petab_problem: petab.Problem
            The PEtab problem.
        """
        if petab_problem is None:
            petab_problem = petab.Problem()
        self.problem = petab_problem
        self.sbml = SbmlViewerModel(
            sbml_model=self.problem.model,
        )
        self.measurement = MeasurementModel(
            data_frame=self.problem.measurement_df,
            type="measurement",
        )
        self.simulation = MeasurementModel(
            data_frame=None,
            type="simulation",
        )
        self.observable = ObservableModel(
            data_frame=self.problem.observable_df,
        )
        self.parameter = ParameterModel(
            data_frame=self.problem.parameter_df, sbml_model=self.sbml
        )
        self.condition = ConditionModel(
            data_frame=self.problem.condition_df,
        )
        self.visualization = VisualizationModel(
            data_frame=self.problem.visualization_df,
        )

    @property
    def models(self):
        return {
            "measurement": self.measurement,
            "observable": self.observable,
            "parameter": self.parameter,
            "condition": self.condition,
            "sbml": self.sbml,
        }

    @property
    def pandas_models(self):
        return {
            "measurement": self.measurement,
            "observable": self.observable,
            "parameter": self.parameter,
            "condition": self.condition,
        }

    @staticmethod
    def from_petab_yaml(
        petab_yaml_path: str,
    ) -> PEtabModel:
        """Create a PEtab model from a PEtab YAML file.

        Parameters
        ----------
        petab_yaml_path: str
            The path to the PEtab YAML file.

        Returns
        -------
        PEtabModel
            The PEtab model.
        """
        petab_problem = petab.Problem.from_yaml(petab_yaml_path)
        return PEtabModel(petab_problem)

    def test_consistency(self) -> bool:
        """Test the consistency of the data.

        Returns
        -------
        bool
            Whether the data is consistent.
        """
        return petab.lint.lint_problem(self.current_petab_problem)

    def save(self, directory: str | Path):
        """Save the PEtab model to a directory.

        Parameters
        ----------
        directory: str
            The directory to save the PEtab model to.
        """
        self.current_petab_problem.to_files_generic(prefix_path=directory)

    def save_as_omex(self, file_name: str):
        """Save the PEtab model as an OMEX file.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            self.save(temp_dir)
            petab.create_combine_archive(
                temp_dir,
                file_name,
                # family_name="", # read from settings
                # given_name="", # read from settings
                # email="", # read from settings
                # organization="", # read from settings
            )

    @property
    def current_petab_problem(self) -> petab.Problem:
        """Get the current PEtab problem.

        Returns
        -------
        petab.Problem
            The current PEtab problem.
        """
        return petab.Problem(
            condition_df=self.condition.get_df(),
            measurement_df=self.measurement.get_df(),
            observable_df=self.observable.get_df(),
            parameter_df=self.parameter.get_df(),
            visualization_df=self.visualization.get_df(),
            model=self.sbml.get_current_sbml_model(),
        )
