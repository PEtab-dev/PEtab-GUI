"""Main Window View."""
from PySide6.QtWidgets import (QApplication, QMainWindow, QDockWidget,
                               QTableView, QWidget, QVBoxLayout, QPushButton, QTabWidget)
from PySide6.QtCore import Qt, Signal, QSettings
from .sbml_view import SbmlViewer
from .table_view import TableViewer
from .task_bar import TaskBar
from .logger import Logger
from .measurement_plot import MeasuremenPlotter


class MainWindow(QMainWindow):
    closing_signal = Signal()

    def __init__(self):
        super().__init__()

        self.allow_close = False

        self.setWindowTitle("PEtab Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Logger: used in both tabs
        self.logger_views = [Logger(self), Logger(self)]

        # Main layout: Two tabs
        self.tab_widget = QTabWidget(self)

        # Tab for the data tables
        self.data_tab = QMainWindow()
        self.tab_widget.addTab(self.data_tab, "Data Tables")

        # Tab for the SBML model
        self.sbml_viewer = SbmlViewer(logger_view=self.logger_views[0])
        self.tab_widget.addTab(self.sbml_viewer, "SBML Model")

        # Set the QTabWidget as the central widget
        self.setCentralWidget(self.tab_widget)

        # Create dock widgets for each table
        self.condition_dock = TableViewer("Condition Table")
        self.measurement_dock = TableViewer("Measurement Table")
        self.observable_dock = TableViewer("Observable Table")
        self.parameter_dock = TableViewer("Parameter Table")
        self.logger_dock = QDockWidget("Info")
        self.logger_dock.setObjectName("logger_dock")
        self.logger_dock.setWidget(self.logger_views[1])
        self.plot_dock = MeasuremenPlotter(self)

        # Add docks to the QMainWindow of the data tab
        self.data_tab.addDockWidget(
            Qt.TopDockWidgetArea,
            self.measurement_dock
        )
        self.data_tab.splitDockWidget(
            self.measurement_dock, self.parameter_dock, Qt.Orientation.Vertical
        )
        self.data_tab.addDockWidget(
            Qt.TopDockWidgetArea,
            self.observable_dock
        )
        self.data_tab.splitDockWidget(
            self.observable_dock, self.condition_dock, Qt.Orientation.Vertical
        )
        self.data_tab.addDockWidget(
            Qt.BottomDockWidgetArea,
            self.logger_dock
        )
        self.data_tab.addDockWidget(
            Qt.BottomDockWidgetArea,
            self.plot_dock
        )
        self.data_tab.tabifyDockWidget(self.plot_dock, self.logger_dock)
        # TODO: Needs better initial sizing. @Frank can you help?
        self.data_tab.resizeDocks(
            [self.logger_dock, self.measurement_dock],
            [self.height() * 0.15, self.height() * 0.3],
            Qt.Vertical
        )


        # Connect the visibility changes of the QDockWidget instances to a slot that saves their visibility status
        self.dock_visibility = {
            self.condition_dock: self.condition_dock.isVisible(),
            self.measurement_dock: self.measurement_dock.isVisible(),
            self.observable_dock: self.observable_dock.isVisible(),
            self.parameter_dock: self.parameter_dock.isVisible(),
            self.logger_dock: self.logger_dock.isVisible(),
            self.plot_dock: self.plot_dock.isVisible(),
        }
        self.condition_dock.visibilityChanged.connect(
            self.save_dock_visibility
        )
        self.measurement_dock.visibilityChanged.connect(
            self.save_dock_visibility
        )
        self.observable_dock.visibilityChanged.connect(
            self.save_dock_visibility
        )
        self.parameter_dock.visibilityChanged.connect(
            self.save_dock_visibility
        )
        self.logger_dock.visibilityChanged.connect(
            self.save_dock_visibility
        )
        self.plot_dock.visibilityChanged.connect(
            self.save_dock_visibility
        )

        # Allow docking in multiple areas
        self.data_tab.setDockOptions(
            QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks
        )

        self.tab_widget.currentChanged.connect(self.set_docks_visible)

        self.load_settings()

        # drag drop
        self.setAcceptDrops(True)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return

        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.controller.open_file(url.toLocalFile())
            return

        event.ignore()
    
    def setup_toolbar(self, actions):
        # add a toolbar with actions from self.task_bar
        tb = self.addToolBar("MainToolbar")
        tb.setObjectName("MainToolbar")
        self.setUnifiedTitleAndToolBarOnMac(True)

        # first the normal open / save operations
        tb.addAction(actions["new"])
        tb.addAction(actions["open"])
        tb.addAction(actions["save"])
        tb.addAction(actions["check_petab"])
        tb.addAction(actions["find+replace"])
        tb.addAction(actions["add_row"])
        tb.addAction(actions["delete_row"])
        tb.addAction(actions["add_column"])
        tb.addAction(actions["delete_column"])
        tb.addWidget(actions["filter_widget"])

    def add_menu_action(self, dock_widget, name):
        """Helper function to add actions to the menu for showing dock widgets"""
        action = self.view_menu.addAction(name)
        action.setCheckable(True)
        action.setChecked(True)

        # Show or hide the dock widget based on the menu action
        action.toggled.connect(lambda checked: dock_widget.setVisible(checked))

        # Sync the menu action with the visibility of the dock widget
        dock_widget.visibilityChanged.connect(action.setChecked)

    def save_dock_visibility(self, visible):
        """Slot to save the visibility status of a QDockWidget when it changes"""
        # if current tab is not the data tab return
        if self.tab_widget.currentIndex() != 0:
            return
        dock = self.sender()  # Get the QDockWidget that emitted the signal
        self.dock_visibility[dock] = dock.isVisible()

    def set_docks_visible(self, index):
        """Slot to set all QDockWidget instances to their previous visibility when the "Data Tables" tab is not selected"""
        if index != 0:  # Another tab is selected
            for dock, visible in self.dock_visibility.items():
                dock.setVisible(visible)

    def closeEvent(self, event):
        """Override the closeEvent to emit a signal and let the controller handle it."""
        # Emit the signal to let the controller decide what to do
        self.closing_signal.emit()

        QApplication.processEvents()

        if self.allow_close:
            self.save_settings()
            event.accept()
        else:
            event.ignore()


    def load_settings(self):
        """Load the settings from the QSettings object."""
        settings = QSettings("petab", "petab_gui")

        # Load the visibility of the dock widgets
        for dock, _ in self.dock_visibility.items():
            dock.setVisible(settings.value(f"docks/{dock.objectName()}", True, type=bool))
                
        # Load the geometry of the main window
        self.restoreGeometry(settings.value("main_window/geometry"))

        # Restore the positions of the dock widgets
        self.restoreState(settings.value("main_window/state"))

        # restore the settings of the data tab
        self.data_tab.restoreGeometry(settings.value("data_tab/geometry"))
        self.data_tab.restoreState(settings.value("data_tab/state"))


    def save_settings(self):
        """Save the settings to the QSettings object."""
        settings = QSettings("petab", "petab_gui")

        # Save the visibility of the dock widgets
        for dock, _ in self.dock_visibility.items():
            settings.setValue(f"docks/{dock.objectName()}", dock.isVisible())

        # Save the geometry of the main window
        settings.setValue("main_window/geometry", self.saveGeometry())

        # Save the positions of the dock widgets
        settings.setValue("main_window/state", self.saveState())

        # save the settings of the data tab
        settings.setValue("data_tab/geometry", self.data_tab.saveGeometry())
        settings.setValue("data_tab/state", self.data_tab.saveState())

