"""Simulation Controller for PEtab GUI.

This module contains the SimulationController class, which handles PEtab model
simulation operations, including:
- Running PEtab simulations using COPASI/basico
- Managing simulation settings
- Handling simulation results and updating the simulation table
"""

import tempfile


class SimulationController:
    """Controller for PEtab simulations.

    Handles execution of PEtab simulations using the basico/COPASI backend.
    Manages simulation settings, runs simulations, and updates the simulation
    results table with the output.

    Attributes
    ----------
    main : MainController
        Reference to the main controller for access to models, views, and other controllers.
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

        # import petabsimualtor
        import basico
        from basico.petab import PetabSimulator

        # report current basico / COPASI version
        self.logger.log_message(
            f"Simulate with basico: {basico.__version__}, COPASI: {basico.COPASI.__version__}",
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
