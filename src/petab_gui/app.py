from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFileOpenEvent
from PySide6.QtCore import QEvent
import sys
import os
import petab.v1 as petab

from .views import MainWindow
from .controllers import MainController
from .models import PEtabModel

from pathlib import Path



def find_example(path: Path) -> Path:
    while path.parent != path:
        if (path / "example").is_dir():
            return path / "example"
        path = path.parent
        
    raise FileNotFoundError("Could not find examples directory")


class PEtabGuiApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        # no need to instantiate a PEtab problem, as we are not using it
        # 
        # petab_problem = petab.Problem.from_yaml(
        #     find_example(Path(__file__).parent) / "problem.yaml"
        # )
        self.model = PEtabModel()
        self.view = MainWindow()
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


def main():
    app = PEtabGuiApp()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
