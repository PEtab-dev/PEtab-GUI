"""Validation Controller for PEtab GUI.

This module contains the ValidationController class, which handles all model
validation operations, including:
- PEtab model consistency checking
- Validation error logging and reporting
- Invalid cell management
"""

import logging

from ..utils import CaptureLogHandler
from .utils import filtered_error


class ValidationController:
    """Controller for model validation.

    Handles validation of PEtab models and reports errors to the user through
    the logging system. Manages the PEtab lint process and coordinates
    validation results with the model's invalid cell tracking.

    Attributes
    ----------
    main : MainController
        Reference to the main controller for access to models, views, and
        other controllers.
    model : PEtabModel
        The PEtab model being validated.
    logger : LoggerController
        The logger for user feedback.
    """

    def __init__(self, main_controller):
        """Initialize the ValidationController.

        Parameters
        ----------
        main_controller : MainController
            The main controller instance.
        """
        self.main = main_controller
        self.model = main_controller.model
        self.logger = main_controller.logger

    def check_model(self):
        """Check the consistency of the model and log the results.

        Runs the PEtab linter to validate the model structure, data, and
        consistency. Captures and reports all validation messages, and
        resets invalid cell markers if validation passes.

        Notes
        -----
        Uses PEtab's built-in validation through `model.test_consistency()`.
        Captures log messages from the PEtab linter for display to the user.
        """
        capture_handler = CaptureLogHandler()
        logger_lint = logging.getLogger("petab.v1.lint")
        logger_vis = logging.getLogger("petab.v1.visualize.lint")
        logger_lint.addHandler(capture_handler)
        logger_vis.addHandler(capture_handler)

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
                self.logger.log_message(
                    "PEtab problem has no errors.", color="green"
                )
                for model in self.model.pandas_models.values():
                    model.reset_invalid_cells()
            else:
                self.logger.log_message(
                    "PEtab problem has errors.", color="red"
                )
        except Exception as e:
            msg = f"PEtab linter failed at some point: {filtered_error(e)}"
            self.logger.log_message(msg, color="red")
        finally:
            # Always remove the capture handler
            logger_lint.removeHandler(capture_handler)
            logger_vis.removeHandler(capture_handler)
