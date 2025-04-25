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
    while path.parent != path:
        if (path / "example").is_dir():
            return path / "example"
        path = path.parent

    raise FileNotFoundError("Could not find examples directory")


def get_icon() -> QIcon:
    """Get the Icon for the Window"""
    icon_path = files("petab_gui.assets").joinpath("PEtab.png")
    if not icon_path.is_file():
        raise FileNotFoundError(f"Icon file not found: {icon_path}")
    icon = QIcon(str(icon_path))
    return icon


class PEtabGuiApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        # Load the stylesheet
        # self.apply_stylesheet()
        self.setWindowIcon(get_icon())
        self.model = PEtabModel()
        self.view = MainWindow()
        self.view.setWindowIcon(get_icon())
        self.controller = MainController(self.view, self.model)

        # hack to be discussed
        self.view.controller = self.controller

        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            self.controller.open_file(sys.argv[1], mode="overwrite")

        self.view.show()

    def event(self, event):
        if event.type() == QEvent.FileOpen:
            openEvent = QFileOpenEvent(event)
            self.controller.open_file(openEvent.file(), mode="overwrite")

        return super().event(event)

    def apply_stylesheet(self):
        """Load and apply the QSS stylesheet."""
        stylesheet_path = os.path.join(
            os.path.dirname(__file__), "stylesheet.css"
        )
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path) as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Warning: Stylesheet '{stylesheet_path}' not found!")


def main():
    app = PEtabGuiApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
