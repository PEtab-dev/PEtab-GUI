"""Simulation Controller for PEtab GUI.

This module contains the SimulationController class, which handles PEtab model
simulation operations, including:
- Running PEtab simulations using COPASI/basico
- Managing simulation settings
- Handling simulation results and updating the simulation table
"""

import tempfile

import petab.v1 as petab


class SimulationController:
    """Controller for PEtab simulations.

    Handles execution of PEtab simulations using the basico/COPASI backend.
    Manages simulation settings, runs simulations, and updates the simulation
    results table with the output.

    Attributes
    ----------
    main : MainController
        Reference to the main controller for access to models, views, and
        other controllers.
    model : PEtabModel
        The PEtab model being simulated.
    logger : LoggerController
        The logger for user feedback.
    simulation_table_controller : MeasurementController
        The controller for the simulation results table.
    """

    def __init__(self, main_controller):
        """Initialize the SimulationController.

        Parameters
        ----------
        main_controller : MainController
            The main controller instance.
        """
        self.main = main_controller
        self.model = main_controller.model
        self.logger = main_controller.logger

    def simulate(self):
        """Simulate the PEtab model using COPASI/basico.

        Runs a simulation of the current PEtab problem using the basico
        library with COPASI as the backend simulator. The simulation results
        are written to the simulation table and invalid cells are cleared.

        Notes
        -----
        Uses a temporary directory for simulation working files.
        Currently configured to use COPASI's CURRENT_SOLUTION method.
        Requires basico and COPASI to be installed.
        """
        # obtain petab problem
        petab_problem = self.model.current_petab_problem

        # Check if nominalValue column exists, if not add it from SBML model
        parameter_df = petab_problem.parameter_df.copy()
        if (
            parameter_df is not None
            and not parameter_df.empty
            and petab.C.NOMINAL_VALUE not in parameter_df.columns
        ):
            self.logger.log_message(
                "nominalValue column missing in parameter table. "
                "Extracting nominal values from SBML model...",
                color="orange",
            )
            # Extract parameter values from SBML model
            sbml_model = self.model.sbml.get_current_sbml_model()
            if sbml_model is not None:
                nominal_values = []
                for param_id in parameter_df.index:
                    try:
                        value = sbml_model.get_parameter_value(param_id)
                        nominal_values.append(value)
                    except Exception:
                        # If parameter not found in SBML, use default value
                        nominal_values.append(1.0)

                # Add nominalValue column to parameter_df
                parameter_df[petab.C.NOMINAL_VALUE] = nominal_values
                self.logger.log_message(
                    f"Successfully extracted {len(nominal_values)} "
                    f"nominal values from SBML model. Add nominalValue "
                    f"column to parameter table to set values manually.",
                    color="green",
                )

                # Update the petab problem with the modified parameter_df
                petab_problem = petab.Problem(
                    condition_df=petab_problem.condition_df,
                    measurement_df=petab_problem.measurement_df,
                    observable_df=petab_problem.observable_df,
                    parameter_df=parameter_df,
                    visualization_df=petab_problem.visualization_df,
                    model=petab_problem.model,
                )

        import basico
        from basico.petab import PetabSimulator

        # report current basico / COPASI version
        self.logger.log_message(
            f"Simulate with basico: {basico.__version__}, "
            f"COPASI: {basico.COPASI.__version__}",
            color="green",
        )

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
        self.main.simulation_table_controller.overwrite_df(sim_df)
        self.main.simulation_table_controller.model.reset_invalid_cells()
