"""Plot Coordinator for PEtab GUI.

This module contains the PlotCoordinator class, which handles all plotting
and selection synchronization operations, including:
- Initializing and updating plot visualizations
- Synchronizing selections between tables and plots
- Handling plot point click interactions
- Managing plot update debouncing
"""

from PySide6.QtCore import Qt, QTimer

from ..utils import get_selected


class PlotCoordinator:
    """Coordinator for plotting and selection synchronization.

    Manages the bidirectional synchronization between table selections and plot
    highlights, handles plot interactions, and coordinates plot updates across
    multiple data views.

    Attributes
    ----------
    main : MainController
        Reference to the main controller for access to models, views, and
        other controllers.
    model : PEtabModel
        The PEtab model being visualized.
    view : MainWindow
        The main application window.
    logger : LoggerController
        The logger for user feedback.
    plotter : PlotDock
        The plot widget for data visualization.
    """

    def __init__(self, main_controller):
        """Initialize the PlotCoordinator.

        Parameters
        ----------
        main_controller : MainController
            The main controller instance.
        """
        self.main = main_controller
        self.model = main_controller.model
        self.view = main_controller.view
        self.logger = main_controller.logger

        # Plot widget reference (set by init_plotter)
        self.plotter = None

        # Selection synchronization flags to prevent redundant updates
        self._updating_from_plot = False
        self._updating_from_table = False

        # Plot update timer for debouncing
        self._plot_update_timer = QTimer()
        self._plot_update_timer.setSingleShot(True)
        self._plot_update_timer.setInterval(0)
        self._plot_update_timer.timeout.connect(self.init_plotter)

    def init_plotter(self):
        """(Re-)initialize the plotter.

        Sets up the plot widget with the current data models and configures
        the click callback for interactive plot point selection.
        """
        self.view.plot_dock.initialize(
            self.main.measurement_controller.proxy_model,
            self.main.simulation_table_controller.proxy_model,
            self.main.condition_controller.proxy_model,
            self.main.visualization_controller.proxy_model,
            self.model,
        )
        self.plotter = self.view.plot_dock
        self.plotter.highlighter.click_callback = self._on_plot_point_clicked

    def handle_selection_changed(self):
        """Update the plot when selection in the measurement table changes.

        This is a convenience method that delegates to update_plot().
        """
        self.update_plot()

    def handle_data_changed(self, top_left, bottom_right, roles):
        """Update the plot when the data in the measurement table changes.

        Parameters
        ----------
        top_left : QModelIndex
            Top-left index of the changed region.
        bottom_right : QModelIndex
            Bottom-right index of the changed region.
        roles : list[int]
            List of Qt item data roles that changed.
        """
        if not roles or Qt.DisplayRole in roles:
            self.update_plot()

    def update_plot(self):
        """Update the plot with the selected measurement data.

        Extracts the selected data points from the measurement table and
        updates the plot visualization with this data. The plot shows all
        data for the selected observables with the selected points highlighted.
        """
        selection_model = (
            self.view.measurement_dock.table_view.selectionModel()
        )
        indexes = selection_model.selectedIndexes()
        if not indexes:
            return

        selected_points = {}
        for index in indexes:
            if index.row() == self.model.measurement.get_df().shape[0]:
                continue
            row = index.row()
            observable_id = self.model.measurement._data_frame.iloc[row][
                "observableId"
            ]
            if observable_id not in selected_points:
                selected_points[observable_id] = []
            selected_points[observable_id].append(
                {
                    "x": self.model.measurement._data_frame.iloc[row]["time"],
                    "y": self.model.measurement._data_frame.iloc[row][
                        "measurement"
                    ],
                }
            )
        if selected_points == {}:
            return

        measurement_data = self.model.measurement._data_frame
        plot_data = {"all_data": [], "selected_points": selected_points}
        for observable_id in selected_points:
            observable_data = measurement_data[
                measurement_data["observableId"] == observable_id
            ]
            plot_data["all_data"].append(
                {
                    "observable_id": observable_id,
                    "x": observable_data["time"].tolist(),
                    "y": observable_data["measurement"].tolist(),
                }
            )

        self.view.plot_dock.update_visualization(plot_data)

    def _schedule_plot_update(self):
        """Start the plot schedule timer.

        Debounces plot updates by using a timer to avoid excessive redraws
        when data changes rapidly.
        """
        self._plot_update_timer.start()

    def _floats_match(self, a, b, epsilon=1e-9):
        """Check if two floats match within epsilon tolerance.

        Parameters
        ----------
        a : float
            First value to compare.
        b : float
            Second value to compare.
        epsilon : float, optional
            Tolerance for comparison (default: 1e-9).

        Returns
        -------
        bool
            True if |a - b| < epsilon, False otherwise.
        """
        return abs(a - b) < epsilon

    def _on_plot_point_clicked(self, x, y, label, data_type):
        """Handle plot point clicks and select corresponding table row.

        Uses epsilon tolerance for floating-point comparison to avoid
        precision issues. Synchronizes the table selection with the clicked
        plot point.

        Parameters
        ----------
        x : float
            X-coordinate of the clicked point (time).
        y : float
            Y-coordinate of the clicked point (measurement or simulation
            value).
        label : str
            Label of the clicked point (observable ID).
        data_type : str
            Type of data: "measurement" or "simulation".
        """
        # Check for None label
        if label is None:
            self.logger.log_message(
                "Cannot select table row: plot point has no label.",
                color="orange",
            )
            return

        # Extract observable ID from label
        proxy = self.main.measurement_controller.proxy_model
        view = self.main.measurement_controller.view.table_view
        if data_type == "simulation":
            proxy = self.main.simulation_table_controller.proxy_model
            view = self.main.simulation_table_controller.view.table_view
        obs = label

        x_axis_col = "time"
        y_axis_col = data_type
        observable_col = "observableId"

        # Get column indices with error handling
        def column_index(name):
            for col in range(proxy.columnCount()):
                if proxy.headerData(col, Qt.Horizontal) == name:
                    return col
            raise ValueError(f"Column '{name}' not found.")

        try:
            x_col = column_index(x_axis_col)
            y_col = column_index(y_axis_col)
            obs_col = column_index(observable_col)
        except ValueError as e:
            self.logger.log_message(
                f"Table selection failed: {e}",
                color="red",
            )
            return

        # Search for matching row using epsilon tolerance for floats
        matched = False
        for row in range(proxy.rowCount()):
            row_obs = proxy.index(row, obs_col).data()
            row_x = proxy.index(row, x_col).data()
            row_y = proxy.index(row, y_col).data()
            try:
                row_x, row_y = float(row_x), float(row_y)
            except ValueError:
                continue

            # Use epsilon tolerance for float comparison
            if (
                row_obs == obs
                and self._floats_match(row_x, x)
                and self._floats_match(row_y, y)
            ):
                # Manually update highlight BEFORE selecting row
                # This ensures the circle appears even though we skip
                # the signal handler
                if data_type == "measurement":
                    self.plotter.highlight_from_selection([row])
                else:
                    self.plotter.highlight_from_selection(
                        [row],
                        proxy=self.main.simulation_table_controller.proxy_model,
                        y_axis_col="simulation",
                    )

                # Set flag to prevent redundant highlight update from signal
                self._updating_from_plot = True
                try:
                    view.selectRow(row)
                    matched = True
                finally:
                    self._updating_from_plot = False
                break

        # Provide feedback if no match found
        if not matched:
            self.logger.log_message(
                f"No matching row found for plot point "
                f"(obs={obs}, x={x:.4g}, y={y:.4g})",
                color="orange",
            )

    def _handle_table_selection_changed(
        self, table_view, proxy=None, y_axis_col="measurement"
    ):
        """Common handler for table selection changes.

        Skips update if selection was triggered by plot click to prevent
        redundant highlight updates. Updates the plot highlights based on
        the current table selection.

        Parameters
        ----------
        table_view : QTableView
            The table view with selection to highlight.
        proxy : QSortFilterProxyModel, optional
            Optional proxy model for simulation data.
        y_axis_col : str, optional
            Column name for y-axis data (default: "measurement").
        """
        # Skip if selection was triggered by plot point click
        if self._updating_from_plot:
            return

        # Set flag to prevent infinite loop if highlight triggers selection
        self._updating_from_table = True
        try:
            selected_rows = get_selected(table_view)
            if proxy:
                self.plotter.highlight_from_selection(
                    selected_rows, proxy=proxy, y_axis_col=y_axis_col
                )
            else:
                self.plotter.highlight_from_selection(selected_rows)
        finally:
            self._updating_from_table = False

    def _on_table_selection_changed(self, selected, deselected):
        """Highlight the cells selected in measurement table.

        Parameters
        ----------
        selected : QItemSelection
            The newly selected items.
        deselected : QItemSelection
            The newly deselected items.
        """
        self._handle_table_selection_changed(
            self.main.measurement_controller.view.table_view
        )

    def _on_simulation_selection_changed(self, selected, deselected):
        """Highlight the cells selected in simulation table.

        Parameters
        ----------
        selected : QItemSelection
            The newly selected items.
        deselected : QItemSelection
            The newly deselected items.
        """
        self._handle_table_selection_changed(
            self.main.simulation_table_controller.view.table_view,
            proxy=self.main.simulation_table_controller.proxy_model,
            y_axis_col="simulation",
        )
