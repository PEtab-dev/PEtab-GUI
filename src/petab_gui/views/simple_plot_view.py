from collections import defaultdict

import qtawesome as qta
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.container import ErrorbarContainer
from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QMenu,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .utils import proxy_to_dataframe


class PlotWorkerSignals(QObject):
    finished = Signal(object)  # Emits final Figure


class PlotWorker(QRunnable):
    def __init__(self, vis_df, cond_df, meas_df, sim_df, group_by):
        super().__init__()
        self.vis_df = vis_df
        self.cond_df = cond_df
        self.meas_df = meas_df
        self.sim_df = sim_df
        self.group_by = group_by
        self.signals = PlotWorkerSignals()

    def run(self):
        # Move all Matplotlib plotting to the GUI thread. Only prepare payload here.
        sim_df = self.sim_df if not self.sim_df.empty else None
        payload = {
            "vis_df": self.vis_df,
            "cond_df": self.cond_df,
            "meas_df": self.meas_df,
            "sim_df": sim_df,
            "group_by": self.group_by,
        }
        self.signals.finished.emit(payload)


class PlotWidget(FigureCanvas):
    def __init__(self):
        self.fig, self.axes = plt.subplots()
        super().__init__(self.fig)


class MeasurementPlotter(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Measurement Plot", parent)
        self.setObjectName("plot_dock")
        self.options_manager = ToolbarOptionManager()

        self.meas_proxy = None
        self.sim_proxy = None
        self.cond_proxy = None
        self.petab_model = None
        self.highlighter = MeasurementHighlighter()

        self.dock_widget = QWidget(self)
        self.layout = QVBoxLayout(self.dock_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.setWidget(self.dock_widget)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.plot_it)
        self.observable_to_subplot = {}

    def initialize(
        self, meas_proxy, sim_proxy, cond_proxy, vis_proxy,
        petab_model
    ):
        self.meas_proxy = meas_proxy
        self.cond_proxy = cond_proxy
        self.sim_proxy = sim_proxy
        self.vis_proxy = vis_proxy
        self.petab_model = petab_model

        # Connect data changes
        self.options_manager.option_changed.connect(self._debounced_plot)
        self.meas_proxy.dataChanged.connect(self._debounced_plot)
        self.meas_proxy.rowsInserted.connect(self._debounced_plot)
        self.meas_proxy.rowsRemoved.connect(self._debounced_plot)
        self.cond_proxy.dataChanged.connect(self._debounced_plot)
        self.cond_proxy.rowsInserted.connect(self._debounced_plot)
        self.cond_proxy.rowsRemoved.connect(self._debounced_plot)
        self.sim_proxy.dataChanged.connect(self._debounced_plot)
        self.sim_proxy.rowsInserted.connect(self._debounced_plot)
        self.sim_proxy.rowsRemoved.connect(self._debounced_plot)
        self.vis_proxy.dataChanged.connect(self._debounced_plot)
        self.vis_proxy.rowsInserted.connect(self._debounced_plot)
        self.vis_proxy.rowsRemoved.connect(self._debounced_plot)
        self.visibilityChanged.connect(self._debounced_plot)

        self.plot_it()

    def plot_it(self):
        if not self.meas_proxy or not self.cond_proxy:
            return
        if not self.isVisible():
            # If the dock is not visible, do not plot
            return

        measurements_df = proxy_to_dataframe(self.meas_proxy)
        simulations_df = proxy_to_dataframe(self.sim_proxy)
        conditions_df = proxy_to_dataframe(self.cond_proxy)
        visualisation_df = proxy_to_dataframe(self.vis_proxy)
        group_by = self.options_manager.get_option()
        # group_by different value in petab.visualize
        if group_by == "condition":
            group_by = "simulation"

        worker = PlotWorker(
            visualisation_df,
            conditions_df,
            measurements_df,
            simulations_df,
            group_by
        )
        worker.signals.finished.connect(self._render_on_main_thread)
        QThreadPool.globalInstance().start(worker)

    def _render_on_main_thread(self, payload):
        import petab.v1.visualize as petab_vis
        # GUI-thread plotting
        plt.close('all')
        meas_df = payload.get('meas_df')
        cond_df = payload.get('cond_df')
        if meas_df is None or meas_df.empty or cond_df is None or cond_df.empty:
            self._update_tabs(None)
            return
        sim_df = payload.get('sim_df')
        group_by = payload.get('group_by')
        if group_by == 'vis_df':
            vis_df = payload.get('vis_df')
            if vis_df is not None and not vis_df.empty:
                try:
                    petab_vis.plot_with_vis_spec(vis_df, cond_df, meas_df, sim_df)
                    fig = plt.gcf()
                    self._update_tabs(fig)
                    return
                except Exception as e:
                    print(f'Invalid Visualisation DF: {e}')
            # fallback to observable grouping
            plt.close('all')
            petab_vis.plot_without_vis_spec(
                cond_df, measurements_df=meas_df, simulations_df=sim_df, group_by='observable'
            )
        else:
            plt.close('all')
            petab_vis.plot_without_vis_spec(
                cond_df, measurements_df=meas_df, simulations_df=sim_df, group_by=group_by
            )
        fig = plt.gcf()
        fig.subplots_adjust(left=0.12, bottom=0.15, right=0.95, top=0.9, wspace=0.3, hspace=0.4)
        self._update_tabs(fig)

    def _update_tabs(self, fig: plt.Figure):
        # Clean previous tabs
        self.tab_widget.clear()
        # Clear Highlighter
        self.highlighter.clear_highlight()
        if fig is None:
            # Fallback: show one empty plot tab
            empty_fig, _ = plt.subplots()
            empty_canvas = FigureCanvas(empty_fig)
            empty_toolbar = CustomNavigationToolbar(empty_canvas, self)

            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            layout.addWidget(empty_toolbar)
            layout.addWidget(empty_canvas)

            self.tab_widget.addTab(tab, "All Plots")
            return

        # Full figure tab
        create_plot_tab(fig, self, plot_title="All Plots")

        # One tab per Axes
        for idx, ax in enumerate(fig.axes):
            # Create a new figure and copy Axes content
            sub_fig, sub_ax = plt.subplots(constrained_layout=False)
            handles, labels = ax.get_legend_handles_labels()
            for handle, label in zip(handles, labels, strict=False):
                if isinstance(handle, ErrorbarContainer):
                    line = handle.lines[0]
                elif isinstance(handle, plt.Line2D):
                    line = handle
                else:
                    continue
                sub_ax.plot(
                    line.get_xdata(),
                    line.get_ydata(),
                    label=label,
                    linestyle=line.get_linestyle(),
                    marker=line.get_marker(),
                    color=line.get_color(),
                    alpha=line.get_alpha(),
                    picker=True,
                )
            sub_ax.set_title(ax.get_title())
            sub_ax.set_xlabel(ax.get_xlabel())
            sub_ax.set_ylabel(ax.get_ylabel())
            sub_ax.legend()

            sub_canvas = create_plot_tab(
                sub_fig,
                self,
                plot_title=f"Subplot {idx + 1}",
            )

            if ax.get_title():
                obs_id = ax.get_title()
            elif ax.get_legend_handles_labels()[1]:
                obs_id = ax.get_legend_handles_labels()[1][0]
                obs_id = obs_id.split(" ")[-1]
            else:
                obs_id = f"subplot_{idx}"

            self.observable_to_subplot[obs_id] = idx
            self.highlighter.register_subplot(ax, idx)
            # Register subplot canvas
            self.highlighter.register_subplot(sub_ax, idx)
            # Also register the original ax from the full figure (main tab)
            self.highlighter.connect_picking(sub_canvas)
        # Plot residuals if necessary
        self.plot_residuals()

    def highlight_from_selection(self, selected_rows: list[int], proxy=None, y_axis_col="measurement"):
        proxy = proxy or self.meas_proxy
        if not proxy:
            return

        x_axis_col = "time"
        observable_col = "observableId"

        def column_index(name):
            for col in range(proxy.columnCount()):
                if proxy.headerData(col, Qt.Horizontal) == name:
                    return col
            raise ValueError(f"Column '{name}' not found in proxy.")

        x_col = column_index(x_axis_col)
        y_col = column_index(y_axis_col)
        obs_col = column_index(observable_col)

        grouped_points = {}  # subplot_idx → list of (x, y)

        for row in selected_rows:
            x = proxy.index(row, x_col).data()
            y = proxy.index(row, y_col).data()
            try:
                x = float(x)
                y = float(y)
            except ValueError:
                pass
            obs = proxy.index(row, obs_col).data()
            subplot_idx = self.observable_to_subplot.get(obs)
            if subplot_idx is not None:
                grouped_points.setdefault(subplot_idx, []).append((x, y))

        for subplot_idx, points in grouped_points.items():
            self.highlighter.update_highlight(subplot_idx, points)

    def _debounced_plot(self):
        self.update_timer.start(1000)

    def plot_residuals(self):
        """Plot residuals between measurements and simulations."""
        if not self.petab_model or not self.sim_proxy:
            return
        if not self.isVisible():
            # If the dock is not visible, do not plot
            return

        problem = self.petab_model.current_petab_problem
        simulations_df = proxy_to_dataframe(self.sim_proxy)

        if simulations_df.empty:
            return

        from petab.v1.visualize.plot_residuals import (
            plot_goodness_of_fit,
            plot_residuals_vs_simulation,
        )
        fig_res, axes = plt.subplots(
            1, 2,
            sharey=True, constrained_layout=True, width_ratios=[2, 1]
        )
        try:
            plot_residuals_vs_simulation(
                problem,
                simulations_df,
                axes = axes,
            )
            create_plot_tab(fig_res, self, "Residuals vs Simulation")
        except ValueError as e:
            print(f"Error plotting residuals: {e}")
        fig_fit, axes_fit = plt.subplots(constrained_layout=False)
        fig_fit.subplots_adjust(left=0.05, right=0.98, bottom=0.05, top=0.98)
        plot_goodness_of_fit(
            problem,
            simulations_df,
            ax = axes_fit,
        )
        # fig_fit.tight_layout()
        create_plot_tab(fig_fit, self, "Goodness of Fit")


class MeasurementHighlighter:
    def __init__(self):
        self.highlight_scatters = defaultdict(list)  # (subplot index) → scatter artist
        self.point_index_map = {}     # (subplot index, observableId, x, y) → row index
        self.click_callback = None

    def clear_highlight(self):
        self.highlight_scatters = defaultdict(list)

    def register_subplot(self, ax, subplot_idx):
        scatter = ax.scatter(
            [], [], s=80, edgecolors='black', facecolors='none', zorder=5
        )
        self.highlight_scatters[subplot_idx].append(scatter)

    def update_highlight(self, subplot_idx, points: list[tuple[float, float]]):
        """Update highlighted points on one subplot."""
        for scatter in self.highlight_scatters.get(subplot_idx, []):
            if points:
                x, y = zip(*points, strict=False)
                scatter.set_offsets(list(zip(x, y, strict=False)))
            else:
                scatter.set_offsets([])
            scatter.figure.canvas.draw_idle()

    def connect_picking(self, canvas):
        canvas.mpl_connect("pick_event", self._on_pick)

    def _on_pick(self, event):
        if not callable(self.click_callback):
            return

        artist = event.artist
        if not hasattr(artist, "get_xdata"):
            return

        ind = event.ind
        xdata = artist.get_xdata()
        ydata = artist.get_ydata()
        ax = artist.axes

        # Try to recover the label from the legend (handle → label mapping)
        handles, labels = ax.get_legend_handles_labels()
        label = None
        for h, l in zip(handles, labels, strict=False):
            if h is artist:
                label_parts = l.split()
                if label_parts[-1] == "simulation":
                    data_type = "simulation"
                    label = label_parts[-2]
                else:
                    data_type = "measurement"
                    label = label_parts[-1]
                break

        for i in ind:
            x = xdata[i]
            y = ydata[i]
            self.click_callback(x, y, label, data_type)


class ToolbarOptionManager(QObject):
    """A Manager, synchronizing the selected option across all toolbars."""

    option_changed = Signal(str)
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolbarOptionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Ensure QObject.__init__ runs only once
        if not self._initialized:
            super().__init__()
            self._selected_option = "observable"
            ToolbarOptionManager._initialized = True

    def set_option(self, option):
        if option != self._selected_option:
            self._selected_option = option
            self.option_changed.emit(option)

    def get_option(self):
        return self._selected_option


class CustomNavigationToolbar(NavigationToolbar2QT):
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)
        self.manager = ToolbarOptionManager()

        self.settings_btn = QToolButton(self)
        self.settings_btn.setIcon(qta.icon("mdi6.cog-outline"))
        self.settings_btn.setPopupMode(QToolButton.InstantPopup)
        self.settings_menu = QMenu(self.settings_btn)
        self.groupy_by_options = {
            grp: QAction(f"Groupy by {grp}", self)
            for grp in ["observable", "dataset", "condition"]
        }
        self.groupy_by_options["vis_df"] = QAction(
            "Use Visualization DF", self
        )
        for grp, action in self.groupy_by_options.items():
            action.setCheckable(True)
            action.triggered.connect(lambda _, grp=grp: self.manager.set_option(grp))
            self.settings_menu.addAction(action)
        self.manager.option_changed.connect(self.update_checked_state)
        self.update_checked_state(self.manager.get_option())
        self.settings_btn.setMenu(self.settings_menu)

        self.addWidget(self.settings_btn)

    def update_checked_state(self, selected_option):
        for action in self.groupy_by_options.values():
            action.setChecked(action.text() == f"Groupy by {selected_option}")


def create_plot_tab(
    figure,
    plotter: MeasurementPlotter,
    plot_title: str = "New Plot"
) -> FigureCanvas:
    """Create a new tab with the given figure and plotter."""
    canvas = FigureCanvas(figure)
    toolbar = CustomNavigationToolbar(canvas, plotter)

    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    layout.addWidget(toolbar)
    layout.addWidget(canvas)

    plotter.tab_widget.addTab(tab, plot_title)
    return canvas
