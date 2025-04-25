import os
import sys
from importlib.resources import files
from pathlib import Path

from PySide6.QtCore import QEvent
from PySide6.QtGui import QFileOpenEvent, QIcon
from PySide6.QtWidgets import QApplication

from .controllers import MainController
from .models import PEtabModel
from .views import MainWindow


def find_example(path: Path) -> Path:
    """Find the example directory by traversing up from the given path.

    Args:
        path: The starting path to search from

    Returns:
        Path: The path to the example directory

    Raises:
        FileNotFoundError: If the example directory cannot be found
    """
    while path.parent != path:
        if (path / "example").is_dir():
            return path / "example"
        path = path.parent

    raise FileNotFoundError("Could not find examples directory")


def get_icon() -> QIcon:
    """Get the Icon for the Window."""
    icon_path = files("petab_gui.assets").joinpath("PEtab.png")
    if not icon_path.is_file():
        raise FileNotFoundError(f"Icon file not found: {icon_path}")
    return QIcon(str(icon_path))


class PEtabGuiApp(QApplication):
    """Main application class for PEtab GUI.

    Inherits from QApplication and sets up the MVC components.
    """

    def __init__(self):
        """Initialize the PEtab GUI application.

        Sets up the model, view, and controller components.
        Handles command line arguments for opening files.
        """
        super().__init__(sys.argv)

        self.setWindowIcon(get_icon())
        self.model = PEtabModel()
        self.view = MainWindow()
        self.view.setWindowIcon(get_icon())
        self.controller = MainController(self.view, self.model)

        # Connect the view to the controller
        self.view.controller = self.controller

        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            self.controller.open_file(sys.argv[1], mode="overwrite")

        self.view.show()

    def event(self, event):
        """Handle application events.

        Args:
            event: The Qt event to handle

        Returns:
            bool: Result of the event handling from the parent class

        Notes:
            Currently handles FileOpen events to open files dropped on
            the application.
        """
        if event.type() == QEvent.FileOpen:
            openEvent = QFileOpenEvent(event)
            self.controller.open_file(openEvent.file(), mode="overwrite")

        return super().event(event)

    def apply_stylesheet(self):
        """Load and apply the QSS stylesheet to the application.

        Reads the stylesheet.css file from the same directory as this module
        and applies it to the application. If the file doesn't exist,
        no stylesheet is applied.
        """
        stylesheet_path = os.path.join(
            os.path.dirname(__file__), "stylesheet.css"
        )
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path) as f:
                self.setStyleSheet(f.read())
        else:
            pass


def main():
    """Entry point for the PEtab GUI application.

    Creates the application instance and starts the event loop.
    The function exits with the return code from the application.
    """
    app = PEtabGuiApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
