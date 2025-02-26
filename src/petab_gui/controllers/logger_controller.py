"""File containing the controller of the logger widget."""
from datetime import datetime

from pyarrow import timestamp


class LoggerController:
    """Mainly responsible for handling the logger widget."""

    def __init__(self, views):
        """Initialize the logger controller.

        Parameters
        ----------
        view: Logger
            The view of the logger widget.
        """
        self.views = views

    def log_message(self, message, color="black"):
        """Log a message to the logger.

        Parameters
        ----------
        message: str
            The message to log.
        color: str
            The color of the message. Default is black.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = \
            f"[{timestamp}]\t <span style='color: {color};'>{message}</span>"
        for view in self.views:
            view.logger.append(full_message)

    def clear_log(self):
        """Clear the logger."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clear_message = f"[{timestamp}]\t Logger cleared."
        for view in self.views:
            view.logger.clear()
            view.logger.append(clear_message)
