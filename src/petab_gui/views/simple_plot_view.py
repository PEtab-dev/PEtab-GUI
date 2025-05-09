from collections import defaultdict

import qtawesome as qta
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
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
    def __init__(self, vis_df, cond_df, meas_df, sim_df):
        super().__init__()
        self.vis_df = vis_df
        self.cond_df = cond_df
        self.meas_df = meas_df
        self.sim_df = sim_df
        self.signals = PlotWorkerSignals()

    def run(self):
        import petab.v1.visualize as petab_vis  # Ensure this is thread-local
        plt.close("all")

        if self.meas_df.empty or self.cond_df.empty:
            self.signals.finished.emit(None)
            return
        sim_df = self.sim_df.copy()
        if sim_df.empty:
            sim_df = None

        try:
            if self.vis_df is not None:
                petab_vis.plot_with_vis_spec(
                    self.vis_df,
                    self.cond_df,
                    self.meas_df,
                    sim_df,
                )
                fig = plt.gcf()
                self.signals.finished.emit(fig)
                return
        except Exception as e:
            print(f"Invalid Visualisation DF: {e}")

        # Fallback
        plt.close("all")
        petab_vis.plot_without_vis_spec(
            self.cond_df,
            measurements_df=self.meas_df,
            simulations_df=sim_df,
        )
        fig = plt.gcf()
        fig.subplots_adjust(left=0.12, bottom=0.15, right=0.95, top=0.9, wspace=0.3, hspace=0.4)
        self.signals.finished.emit(fig)


class PlotWidget(FigureCanvas):
    def __init__(self):
        self.fig, self.axes = plt.subplots()
        super().__init__(self.fig)


class MeasurementPlotter(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Measurement Plot", parent)
        self.setObjectName("plot_dock")

        self.meas_proxy = None
        self.sim_proxy = None
        self.cond_proxy = None
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

    def initialize(self, meas_proxy, sim_proxy, cond_proxy):
        self.meas_proxy = meas_proxy
        self.cond_proxy = cond_proxy
        self.sim_proxy = sim_proxy
        self.vis_df = None

        # Connect data changes
        self.meas_proxy.dataChanged.connect(self._debounced_plot)
        self.meas_proxy.rowsInserted.connect(self._debounced_plot)
        self.meas_proxy.rowsRemoved.connect(self._debounced_plot)
        self.cond_proxy.dataChanged.connect(self._debounced_plot)
        self.cond_proxy.rowsInserted.connect(self._debounced_plot)
        self.cond_proxy.rowsRemoved.connect(self._debounced_plot)
        self.sim_proxy.dataChanged.connect(self._debounced_plot)
        self.sim_proxy.rowsInserted.connect(self._debounced_plot)
        self.sim_proxy.rowsRemoved.connect(self._debounced_plot)

        self.plot_it()

    def plot_it(self):
        if not self.meas_proxy or not self.cond_proxy:
            return

        measurements_df = proxy_to_dataframe(self.meas_proxy)
        simulations_df = proxy_to_dataframe(self.sim_proxy)
        conditions_df = proxy_to_dataframe(self.cond_proxy)

        worker = PlotWorker(
            self.vis_df, conditions_df, measurements_df, simulations_df
        )
        worker.signals.finished.connect(self._update_tabs)
        QThreadPool.globalInstance().start(worker)

    def _update_tabs(self, fig: plt.Figure):
        # Clean previous tabs
        self.tab_widget.clear()
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
        full_canvas = FigureCanvas(fig)
        full_toolbar = CustomNavigationToolbar(full_canvas, self)

        full_tab = QWidget()
        full_layout = QVBoxLayout(full_tab)
        full_layout.setContentsMargins(0, 0, 0, 0)
        full_layout.setSpacing(2)
        full_layout.addWidget(full_toolbar)
        full_layout.addWidget(full_canvas)

        self.tab_widget.addTab(full_tab, "All Plots")

        # One tab per Axes
        for idx, ax in enumerate(fig.axes):
            # Create a new figure and copy Axes content
            sub_fig, sub_ax = plt.subplots(constrained_layout=True)
            for line in ax.get_lines():
                sub_ax.plot(
                    line.get_xdata(),
                    line.get_ydata(),
                    label=line.get_label(),
                    linestyle=line.get_linestyle(),
                    marker=line.get_marker(),
                    color=line.get_color(),
                    alpha=line.get_alpha(),
                    picker=True,
                )
            sub_ax.set_title(ax.get_title())
            sub_ax.set_xlabel(ax.get_xlabel())
            sub_ax.set_ylabel(ax.get_ylabel())
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                sub_ax.legend(handles=handles, labels=labels, loc="best")

            sub_canvas = FigureCanvas(sub_fig)
            sub_toolbar = CustomNavigationToolbar(sub_canvas, self)

            sub_tab = QWidget()
            sub_layout = QVBoxLayout(sub_tab)
            sub_layout.setContentsMargins(0, 0, 0, 0)
            sub_layout.setSpacing(2)
            sub_layout.addWidget(sub_toolbar)
            sub_layout.addWidget(sub_canvas)

            self.tab_widget.addTab(sub_tab, f"Subplot {idx + 1}")
            if ax.get_title():
                obs_id = ax.get_title()
            elif ax.get_legend_handles_labels()[1]:
                obs_id = ax.get_legend_handles_labels()[1][0]
                obs_id = obs_id.split(" ")[-1]
            else:
                obs_id = f"subplot_{idx}"

            self.observable_to_subplot[obs_id] = idx
            # Also register the original ax from the full figure (main tab)
            self.highlighter.register_subplot(ax, idx)
            # Register subplot canvas
            self.highlighter.register_subplot(sub_ax, idx)
            self.highlighter.connect_picking(sub_canvas)

    def highlight_from_selection(self, selected_rows: list[int], proxy=None, y_axis_col="measurement"):
        proxy = proxy or self.meas_proxy
        if not proxy:
            return

        # x_axis_col = self.x_axis_selector.currentText()
        x_axis_col = "time"
        y_axis_col = "measurement" if proxy == self.meas_proxy else "simulation"
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

    def update_visualization(self, plot_data):
        print("OK")
        return


class MeasurementHighlighter:
    def __init__(self):
        self.highlight_scatters = defaultdict(list)  # (subplot index) → scatter artist
        self.point_index_map = {}     # (subplot index, observableId, x, y) → row index
        self.click_callback = None

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
        label = ax.get_legend().texts[1].get_text().split()[-1]

        for i in ind:
            x = xdata[i]
            y = ydata[i]
            self.click_callback(x, y, label)


class CustomNavigationToolbar(NavigationToolbar2QT):
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)

        self.settings_btn = QToolButton(self)
        self.settings_btn.setIcon(qta.icon("mdi6.cog-outline"))
        self.settings_btn.setPopupMode(QToolButton.InstantPopup)
        self.settings_menu = QMenu(self.settings_btn)
        self.settings_menu.addAction("Option 1")
        self.settings_menu.addAction("Option 2")
        self.settings_btn.setMenu(self.settings_menu)

        self.addWidget(self.settings_btn)
